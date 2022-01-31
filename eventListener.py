import importlib
from datetime import datetime, timedelta
from typing import Optional, Union, cast

from discord import Game, Message, RawReactionActionEvent
from discord.ext.commands import Cog
from discord.partial_emoji import PartialEmoji
from discord.user import User

import config as cfg
import messageFunctions as msgFnc
from errors import EventNotFound, RoleNotFound, RoleTaken, UnknownEmoji
from event import Event
from eventDatabase import EventDatabase
from operationbot import OperationBot
from role import Role


class EventListener(Cog):

    def __init__(self, bot: OperationBot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        print("Waiting until ready")
        await self.bot.wait_until_ready()
        self.bot.fetch_data()
        commandchannel = self.bot.commandchannel
        await commandchannel.send("Connected")
        print("Ready, importing")
        await commandchannel.send("Importing events")
        await self.bot.import_database()
        await commandchannel.send("Syncing")
        await msgFnc.syncMessages(EventDatabase.events, self.bot)
        await commandchannel.send("Synced")
        EventDatabase.toJson()
        msg = f"{len(EventDatabase.events)} events imported"
        print(msg)
        await commandchannel.send(msg)
        await self.bot.change_presence(activity=Game(name=cfg.GAME))
        print('Logged in as', self.bot.user.name, self.bot.user.id)
        self.bot.processing = False

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):

        if payload.member == self.bot.user or \
                payload.channel_id != self.bot.eventchannel.id:
            # Bot's own reaction, or reaction outside of the event channel
            return

        if payload.emoji.name in cfg.IGNORED_EMOJIS:
            return

        message: Message = await self.bot.eventchannel.fetch_message(
            payload.message_id)
        if message.author != self.bot.user:
            # We don't care about reactions to other messages than our own.
            # Makes it easier to test multiple bot instances on the same
            # channel
            return

        # The member is always defined because we're in the event channel
        user = cast(User, payload.member)
        await message.remove_reaction(payload.emoji, user)

        # Get event from database with message ID
        try:
            event: Event = EventDatabase.getEventByMessage(message.id)
        except EventNotFound as e:
            print(e)
            await self.bot.logchannel.send(
                "NOTE: reaction to a non-existent event. "
                f"msg: {message.id} role: {payload.emoji} "
                f"user: {user.display_name} "
                f"({user.name}#{user.discriminator})\n"
                f"{message.jump_url}")
            return
        else:
            if payload.emoji.is_custom_emoji():
                emoji: Union[PartialEmoji, str] = payload.emoji
            else:
                emoji = cast(str, payload.emoji.name)

            if payload.emoji.name in cfg.SPECIAL_EMOJIS:
                await self._handle_special_emoji(event, emoji, user,
                                                 message)
            else:
                await self._handle_signup(event, emoji, user, message)

    async def _handle_signup(self, event: Event,
                             emoji: Union[PartialEmoji, str], user: User,
                             message: Message):
        # Find signup of user
        old_signup: Optional[Role] = event.findSignupRole(user.id)

        # If a user is already signed up as Zeus they can't sign off or change
        # roles without the Event Moderator
        if old_signup and old_signup.name == cfg.EMOJI_ZEUS:
            return

        # Get role with the emoji
        # TODO: remove when converter exists
        try:
            role = event.findRoleWithEmoji(emoji)
        except RoleNotFound as e:
            raise RoleNotFound(f"{str(e)} in event {event} by user "
                               f"{user.name}#{user.discriminator}") from e

        if role.name == cfg.EMOJI_ZEUS:
            # Somebody with Nitro added the ZEUS reaction by hand, ignoring
            return

        late_signoff_delta = None
        old_role = ""

        # if user is not signed up and the role is free, sign up
        # if user is not signed up and the role is not free, do nothing
        # if user is signed up and they select the same role, sign off
        # if user is signed up and they select a different role,
        #    change to that role
        if old_signup and emoji == old_signup.emoji:
            # User clicked a reaction of the current signed up role
            removed_role = event.undoSignup(user)
            message_action = "SIGNOFF"
        else:
            try:
                removed_role, _ = event.signup(role, user)
            except RoleTaken:
                # Users can't take priority with a reaction
                return
            if removed_role is None:
                # User wasn't signed up to any roles previously
                message_action = "SIGNUP"
            else:
                # User switched from a different role
                message_action = "CHANGE"
                old_role = f"{removed_role.display_name} -> "

        # Update discord embed
        await msgFnc.updateMessageEmbed(message, event)
        EventDatabase.toJson()

        delta_message = ""
        if removed_role and not event.sideop:
            # User signed off or changed role, checking if there's a need to
            # ping
            late_signoff_delta = self._calculate_signoff_delta(
                event, removed_role, user)
            if late_signoff_delta is not None and not event.sideop:
                delta_message = (f"{self.bot.signoff_notify_user.mention}: "
                                 f"{late_signoff_delta} before the "
                                 "operation:\n")

        text = f"{delta_message}{message_action}: {event}, role: " \
               f"{old_role}{role.display_name}, " \
               f"user: {user.display_name} " \
               f"({user.name}#{user.discriminator})"

        await self.bot.logchannel.send(text)

    async def _handle_special_emoji(self, event: Event,
                                    emoji: Union[PartialEmoji, str],
                                    user: User, message: Message):

        if emoji == cfg.ATTENDANCE_EMOJI:
            if event.has_attendee(user):
                event.remove_attendee(user)
            else:
                event.add_attendee(user)
            await msgFnc.updateMessageEmbed(message, event)
            EventDatabase.toJson()
        else:
            raise UnknownEmoji(f"Reaction to unknown special emoji {emoji} "
                               f"in event {event} by user {user}")

    @Cog.listener()
    async def on_message(self, message: Message):
        if message.author == self.bot.user:
            return
        if message.guild is None:
            owner = self.bot.owner
            await owner.send(f"DM: [{message.author}]: {message.content}")

    def _calculate_signoff_delta(self, event: Event, role: Role, user):
        """return a string (days or hours/mins) if it is shortly before op
        else None"""
        if role.name in cfg.SIGNOFF_NOTIFY_ROLES[event.platoon_size]:
            time_delta = event.date - datetime.today()
            if time_delta > timedelta(days=0):
                days = time_delta.days
                hours = time_delta.seconds // (60 * 60)
                mins = (time_delta.seconds - hours * 60 * 60) // 60
                if days > 0:
                    timeframe = f"{days} days"
                else:
                    timeframe = f"{hours}h{mins}min"
                if time_delta < cfg.SIGNOFF_NOTIFY_TIME and \
                        self.bot.signoff_notify_user != user:
                    return timeframe
        return None


def setup(bot: OperationBot):
    importlib.reload(cfg)
    bot.add_cog(EventListener(bot))
