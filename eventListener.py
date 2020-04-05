import importlib
from datetime import datetime, timedelta

from discord import Game, Member, Message, RawReactionActionEvent, Reaction
from discord.ext.commands import Cog

import config as cfg
import messageFunctions as msgFnc
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
        # TODO: add conditional message creation
        # if debug:
        #   create messages
        # else:
        #   detect existing messages
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

        # Remove the reaction
        message = await self.bot.eventchannel.fetch_message(payload.message_id)
        user = payload.member
        await message.remove_reaction(payload.emoji, user)

        # Get event from database with message ID
        event: Event = EventDatabase.getEventByMessage(message.id)
        if event is None:
            print("No event found with that id", message.id)
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
        signup: Role = event.findSignupRole(user.id)

        # Get role with the emoji
        role = event.findRoleWithEmoji(emoji)
        if role is None or role.name == "ZEUS":
            # No role found, or somebody with Nitro added the ZEUS
            # reaction by hand
            print("No role found with that emoji {} in event {} by user {}#{}"
                  .format(emoji, event, user.name, user.discriminator))
            return

        late_signoff = False

        """
        if user is not signed up and the role is     free, sign up
        if user is not signed up and the role is not free, do nothing
        if user is     signed up and they select    the same role, sign off
        if user is     signed up and they select a different role, do nothing
        """
        if signup is None:

            # Sign up if role is free
            if role.userID is None:
                # signup
                event.signup(role, user)

                # Update event
                await msgFnc.updateMessageEmbed(message, event)
                EventDatabase.toJson()
            else:
                # Role is already taken, ignoring sign up attempt
                return
            message_action = "Signup"

        elif signup.emoji == emoji:
            # undo signup
            event.undoSignup(user)

            # Update event
            await msgFnc.updateMessageEmbed(message, event)
            EventDatabase.toJson()

            message_action = "Signoff"

            print("Signed off role name:", role.name)
            if role.name in cfg.SIGNOFF_NOTIFY_ROLES:
                print("Signoff in to be notified")
                date = event.date
                print("Event date:", date)
                time_delta = date - datetime.today()
                if time_delta > timedelta(days=0):
                    days_str = ""
                    hours_str = ""
                    minutes_str = ""
                    days = time_delta.days
                    hours = time_delta.seconds // (60 * 60)
                    minutes = (time_delta.seconds - hours * 60 * 60) // 60
                    if days > 0:
                        days_str = "{} days ".format(days)
                    if hours > 0:
                        hours_str = "{} hours ".format(hours)
                    if minutes > 0:
                        minutes_str = "{} minutes".format(minutes)

                    timestring = "{}{}{}".format(days_str, hours_str,
                                                 minutes_str)

                    if time_delta < cfg.SIGNOFF_NOTIFY_TIME:
                        print("Delta:", time_delta)
                        print("Date delta smaller than notify period")
                        late_signoff = True
        else:
            # user reacted to another role while signed up
            return

        if late_signoff:
            message = "{}: User {} ({}#{}) signed off from {} role {} " \
                      "{} before the operation." \
                      .format(self.bot.signoff_notify_user.mention,
                              user.display_name,
                              user.name,
                              user.discriminator,
                              event,
                              role.emoji,
                              timestring)
        else:
            message = "{}: event: {} role: {} user: {} ({}#{})" \
                      .format(message_action, event, emoji,
                              user.display_name,
                              user.name,
                              user.discriminator)

        await self.bot.logchannel.send(message)

    @Cog.listener()
    async def on_message(self, message: Message):
        if message.author == self.bot.user:
            return
        if message.guild is None:
            owner = self.bot.owner
            await owner.send("DM: [{}]: {}".format(
                message.author, message.content))


def setup(bot: OperationBot):
    importlib.reload(cfg)
    bot.add_cog(EventListener(bot))
