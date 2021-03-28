import importlib
from datetime import datetime, timedelta
from typing import Optional

from discord import Game, Message, RawReactionActionEvent
from discord.ext.commands import Cog

import config as cfg
import messageFunctions as msgFnc
from errors import EventNotFound, RoleNotFound
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
        # await EventDatabase.fromJson(self.bot)
        await self.bot.import_database()
        await commandchannel.send("syncing")
        await msgFnc.syncMessages(EventDatabase.events, self.bot)
        await commandchannel.send("synced")
        EventDatabase.toJson()
        msg = "{} events imported".format(len(EventDatabase.events))
        print(msg)
        await commandchannel.send(msg)
        await self.bot.change_presence(activity=Game(name=cfg.GAME, type=2))
        print('Logged in as', self.bot.user.name, self.bot.user.id)

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):

        if payload.member == self.bot.user or \
                payload.channel_id != self.bot.eventchannel.id:
            # Bot's own reaction, or reaction outside of the event channel
            return

        if payload.emoji.name in cfg.EXTRA_EMOJIS:
            return

        message: Message = await self.bot.eventchannel.fetch_message(
            payload.message_id)
        if message.author != self.bot.user:
            # We don't care about reactions to other messages than our own.
            # Makes it easier to test multiple bot instances on the same
            # channel
            return

        # Remove the reaction
        message = await self.bot.eventchannel.fetch_message(payload.message_id)
        user: User = payload.member
        await message.remove_reaction(payload.emoji, user)

        # Get event from database with message ID
        try:
            event: Event = EventDatabase.getEventByMessage(message.id)
        except EventNotFound as e:
            print(e)
            await self.bot.logchannel.send(
                "NOTE: reaction to a non-existent event. "
                "msg: {} role: {} user: {} ({}#{})"
                .format(message.id, payload.emoji,
                        user.display_name,
                        user.name, user.discriminator))
            return

        # Get emoji string
        if payload.emoji.is_custom_emoji():
            emoji = payload.emoji
        else:
            emoji = payload.emoji.name

        # Find signup of user
        signup: Optional[Role] = event.findSignupRole(user.id)

        # Get role with the emoji
        # TODO: remove when converter exists
        try:
            role = event.findRoleWithEmoji(emoji)
        except RoleNotFound as e:
            raise RoleNotFound("{} in event {} by user {}#{}"
                               .format(str(e), event, user.name,
                                       user.discriminator))

        if role.name == "ZEUS":
            # Somebody with Nitro added the ZEUS reaction by hand, ignoring
            return

        late_signoff_delta = None
        old_role = ""

        """
        if user is not signed up and the role is     free, sign up
        if user is not signed up and the role is not free, do nothing
        if user is     signed up and they select    the same role, sign off
        if user is     signed up and they select a different role, do nothing
        """
        if signup is None:
            self.signup_user(event, role, user)
            message_action = "SIGNUP"
        else:
            removed_role = event.undoSignup(user)
            result = self.signoff_or_change_user(event, role, user, signup,
                                                 emoji)
            if result is None:
                message_action = "SIGNOFF"
            else:
                message_action = "CHANGE"
                old_role = "{} -> ".format(removed_role.display_name)
            late_signoff_delta = self.calculate_signoff_delta(
                event, removed_role, user)

        # Update discord embed
        await msgFnc.updateMessageEmbed(message, event)
        EventDatabase.toJson()
        if message_action is None:
            return

        delta_message = ""

        # ping Moderator if shortly before op
        # else without ping
        if late_signoff_delta is not None and not event.sideop:
            delta_message = "{}: {} before the operation:\n" \
                            .format(self.bot.signoff_notify_user.mention,
                                    late_signoff_delta)

        message = f"{delta_message}{message_action}: {event}, role: " \
                  f"{old_role}{role.display_name}, user: {user.display_name} " \
                  f"({user.name}#{user.discriminator})"

        await self.bot.logchannel.send(message)

    @Cog.listener()
    async def on_message(self, message: Message):
        if message.author == self.bot.user:
            return
        if message.guild is None:
            owner = self.bot.owner
            await owner.send("DM: [{}]: {}".format(
                message.author, message.content))

    # return the signed up role if its empty
    # else None
    def signup_user(self, event: Event, role: Role, user) -> Role:
        if role.userID is None:
            event.signup(role, user)
            return role
        return None

    # return None
    # else the newly signed up role
    def signoff_or_change_user(self, event: Event,  role: Role, user,
                               signup: Optional[Role], emoji) -> Role:
        if signup.emoji == emoji:
            return None
        return self.signup_user(event, role, user)

    def calculate_signoff_delta(self, event: Event, role: Role, user):
        """return a string (days or hours/mins) if it is shortly before op
        else None"""
        if role.name in cfg.SIGNOFF_NOTIFY_ROLES[event.platoon_size]:
            time_delta = event.date - datetime.today()
            if time_delta > timedelta(days=0):
                days = time_delta.days
                hours = time_delta.seconds // (60 * 60)
                mins = (time_delta.seconds - hours * 60 * 60) // 60
                if days > 0:
                    timeframe = "{} days".format(days)
                else:
                    timeframe = "{}h{}min".format(hours, mins)
                if time_delta < cfg.SIGNOFF_NOTIFY_TIME and \
                        self.bot.signoff_notify_user != user:
                    return timeframe
        return None


def setup(bot: OperationBot):
    importlib.reload(cfg)
    bot.add_cog(EventListener(bot))
