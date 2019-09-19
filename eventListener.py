import importlib

from discord import Game, Member, Message, Reaction
from discord.ext.commands import Cog

import config as cfg
from eventDatabase import EventDatabase
from operationbot import OperationBot
from secret import ADMIN


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

        log_channel = self.bot.log_channel
        # Remove the reaction
        await reaction.message.remove_reaction(reaction, user)

        # Get event from database with message ID
        reactedEvent = EventDatabase.getEventByMessage(reaction.message.id)
        if reactedEvent is None:
            print("No event found with that id", reaction.message.id)
            await log_channel.send("NOTE: reaction to a non-existent event. "
                                   "msg: {} role: {} user: {}#{}"
                                   .format(reaction.message.id, reaction.emoji,
                                           user.name, user.discriminator))
            return

        # Get emoji string
        emoji = reaction.emoji

        # Find signup of user
        signup = reactedEvent.findSignup(user.id)

        """
        if user is not signed up and the role is     free, sign up
        if user is not signed up and the role is not free, do nothing
        if user is     signed up and they select    the same role, sign off
        if user is     signed up and they select a different role, do nothing
        """
        if signup is None:
            # Get role with the emoji
            role = reactedEvent.findRoleWithEmoji(emoji)
            if role is None or role.name == "ZEUS":
                # No role found, or somebody with Nitro added the ZEUS
                # reaction by hand
                print("No role found with that emoji {} in event {}"
                      "by user {}#{}"
                      .format(emoji, reactedEvent,
                              user.name, user.discriminator))
                return

            # Sign up if role is free
            if role.userID is None:
                # signup
                reactedEvent.signup(role, user)

                # Update event
                await EventDatabase.updateEvent(reaction.message,
                                                reactedEvent)
                EventDatabase.toJson()
            await log_channel.send("Signup: event: {} role: {} user: {}#{}"
                                   .format(reactedEvent, reaction.emoji,
                                           user.name, user.discriminator))
        elif signup.emoji == emoji:
            # undo signup
            reactedEvent.undoSignup(user)

            # Update event
            await EventDatabase.updateEvent(reaction.message,
                                            reactedEvent)
            EventDatabase.toJson()
            await log_channel.send("Signoff: event: {} role: {} user: {}#{}"
                                   .format(reactedEvent, reaction.emoji,
                                           user.name, user.discriminator))

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
