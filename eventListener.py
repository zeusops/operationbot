import importlib
from datetime import datetime, timedelta

from discord import Game, Member, Message, Reaction
from discord.ext.commands import Cog

import config as cfg
from eventDatabase import EventDatabase
from operationbot import OperationBot
from secret import SIGNOFF_NOTIFY_USER


class EventListener(Cog):

    def __init__(self, bot: OperationBot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        print("Waiting until ready")
        await self.bot.wait_until_ready()
        self.bot.fetch_data()
        commandchannel = self.bot.commandchannel
        print("Ready, importing")
        await commandchannel.send("Importing events")
        await EventDatabase.fromJson(self.bot)
        print("Imported")
        await commandchannel.send("Events imported")
        await self.bot.change_presence(activity=Game(name=cfg.GAME,
                                                     type=2))
        print('Logged in as', self.bot.user.name, self.bot.user.id)

    # Create event command
    @Cog.listener()
    async def on_reaction_add(self, reaction: Reaction, user: Member):
        # Exit if reaction is from the bot or not in the event channel
        if user == self.bot.user \
                or reaction.message.channel != self.bot.eventchannel:
            return

        logchannel = self.bot.logchannel
        # Remove the reaction
        await reaction.message.remove_reaction(reaction, user)

        # Get event from database with message ID
        event = EventDatabase.getEventByMessage(reaction.message.id)
        if event is None:
            print("No event found with that id", reaction.message.id)
            await logchannel.send("NOTE: reaction to a non-existent event. "
                                   "msg: {} role: {} user: {}#{}"
                                   .format(reaction.message.id, reaction.emoji,
                                           user.name, user.discriminator))
            return

        # Get emoji string
        emoji = reaction.emoji

        # Find signup of user
        signup = event.findSignup(user.id)

        # Get role with the emoji
        role = event.findRoleWithEmoji(emoji)
        if role is None or role.name == "ZEUS":
            # No role found, or somebody with Nitro added the ZEUS
            # reaction by hand
            print("No role found with that emoji {} in event {}"
                    "by user {}#{}"
                    .format(emoji, event,
                            user.name, user.discriminator))
            return

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
                await EventDatabase.updateEvent(reaction.message,
                                                event)
                EventDatabase.toJson()
            await logchannel.send("Signup: event: {} role: {} user: {}#{}"
                                   .format(event, reaction.emoji,
                                           user.name, user.discriminator))
        elif signup.emoji == emoji:
            # undo signup
            event.undoSignup(user)

            # Update event
            await EventDatabase.updateEvent(reaction.message,
                                            event)
            EventDatabase.toJson()

            message = "Signoff: event: {} role: {} user: {}#{}" \
                      .format(event, reaction.emoji,
                              user.name, user.discriminator)

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
                    if time_delta.days > 0:
                        days_str = "{} days ".format(time_delta.days)
                if hours > 0:
                    hours_str = "{} hours ".format(hours)
                if minutes > 0:
                    minutes_str = "{} minutes".format(minutes)

                    timestring = "{}{}{}".format(days_str, hours_str,
                                                 minutes_str)

                    if time_delta < cfg.SIGNOFF_NOTIFY_TIME:
                        print("Delta:", time_delta)
                    print("Date delta smaller than notify period")
                    message = "{}: User {} signed off from {} role {} " \
                              "{} before the operation." \
                              .format(self.bot.signoff_notify_user.mention,
                                      user.nick,
                                      event,
                                      role.emoji,
                                      timestring)


            await logchannel.send(message)

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
