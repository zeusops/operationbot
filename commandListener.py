import importlib
from discord.ext import commands
import event
import config as cfg
from main import eventDatabase


class CommandListener:

    def __init__(self, bot):
        self.bot = bot
        self.eventDatabase = eventDatabase

    # Create event command
    @commands.command(pass_context=True, name="create", brief="")
    async def createEvent(self, ctx):
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")

        # Exit if not enough info
        if (len(info) < 2):
            await ctx.send("No date specified")
            return

        # Get event data
        date = info[1]
        eventchannel = self.bot.get_channel(cfg.EVENT_CHANNEL)

        # Create event
        await self.eventDatabase.createEvent(date, ctx.guild.emojis,
                                             eventchannel)

    # Add additional role to event command
    @commands.command(pass_context=True, name="addrole", brief="")
    async def addRole(self, ctx):
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")

        # Get eventchannel
        eventchannel = self.bot.get_channel(cfg.EVENT_CHANNEL)

        # Get data
        try:
            messageID = int(info[1])
        except Exception:
            await ctx.send("Invalid message ID, needs to be an integer")
            return

        # Get roleName
        roleName = ""
        for word in info[2:]:
            roleName += " " + word

        # Get message, return if not found
        try:
            eventMessage = await eventchannel.get_message(messageID)
        except Exception:
            await ctx.send("No message found with that message ID")
            return

        # Find event with messageID
        try:
            eventToUpdate = self.eventDatabase.findEvent(messageID)
        except Exception:
            await ctx.send("No event found with that message ID")
            return

        # Add role
        reaction = eventToUpdate.addAdditionalRole(roleName)

        # Update event
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)

        # Add reaction for role
        await self.eventDatabase.addReaction(eventMessage, reaction)

    # Add additional role to event command
    @commands.command(pass_context=True, name="removerole", brief="")
    async def removeRole(self, ctx):
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")

        # Get eventchannel
        eventchannel = self.bot.get_channel(cfg.EVENT_CHANNEL)

        # Get data
        try:
            messageID = int(info[1])
        except Exception:
            await ctx.send("Invalid message ID, needs to be an integer")
            return

        # Get roleName
        roleName = ""
        for word in info[2:]:
            roleName += " " + word

        # Get message, return if not found
        try:
            eventMessage = await eventchannel.get_message(messageID)
        except Exception:
            await ctx.send("No message found with that message ID")
            return

        # Find event with messageID
        try:
            eventToUpdate = self.eventDatabase.findEvent(messageID)
        except Exception:
            await ctx.send("No event found with that message ID")
            return

        # Remove additional reactions
        for reaction in eventToUpdate.getReactionsOfGroup("Additional"):
            await eventMessage.remove_reaction(reaction, self.bot.user)

        # Remove role
        eventToUpdate.removeAdditionalRole(roleName)

        # Update event
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)

        # Add additional reactions
        for reaction in eventToUpdate.getReactionsOfGroup("Additional"):
            await self.eventDatabase.addReaction(eventMessage, reaction)

    # Add additional role to event command
    @commands.command(pass_context=True, name="settitle", brief="")
    async def setTitle(self, ctx):
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")

        # Get eventchannel
        eventchannel = self.bot.get_channel(cfg.EVENT_CHANNEL)

        # Get data
        try:
            messageID = int(info[1])
        except Exception:
            await ctx.send("Invalid message ID, needs to be an integer")
            return

        # Get newTitle
        newTitle = ""
        for word in info[2:]:
            newTitle += " " + word

        # Get message, return if not found
        try:
            eventMessage = await eventchannel.get_message(messageID)
        except Exception:
            await ctx.send("No message found with that message ID")
            return

        # Find event with messageID
        try:
            eventToUpdate = self.eventDatabase.findEvent(messageID)
        except Exception:
            await ctx.send("No event found with that message ID")
            return

        # Change title
        eventToUpdate.setTitle(newTitle)

        # Update event
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)

    # Add additional role to event command
    @commands.command(pass_context=True, name="setdate", brief="")
    async def setDate(self, ctx):
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")

        # Get eventchannel
        eventchannel = self.bot.get_channel(cfg.EVENT_CHANNEL)

        # Get data
        try:
            messageID = int(info[1])
        except Exception:
            await ctx.send("Invalid message ID, needs to be an integer")
            return

        # Get newDate
        newDate = ""
        for word in info[2:]:
            newDate += " " + word

        # Get message, return if not found
        try:
            eventMessage = await eventchannel.get_message(messageID)
        except Exception:
            await ctx.send("No message found with that message ID")
            return

        # Find event with messageID
        try:
            eventToUpdate = self.eventDatabase.findEvent(messageID)
        except Exception:
            await ctx.send("No event found with that message ID")
            return

        # Change date
        eventToUpdate.setDate(newDate)

        # Update event
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)

    # Add additional role to event command
    @commands.command(pass_context=True, name="settime", brief="")
    async def setTime(self, ctx):
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")

        # Get eventchannel
        eventchannel = self.bot.get_channel(cfg.EVENT_CHANNEL)

        # Get data
        try:
            messageID = int(info[1])
        except Exception:
            await ctx.send("Invalid message ID, needs to be an integer")
            return

        # Get newTime
        newTime = ""
        for word in info[2:]:
            newTime += " " + word

        # Get message, return if not found
        try:
            eventMessage = await eventchannel.get_message(messageID)
        except Exception:
            await ctx.send("No message found with that message ID")
            return

        # Find event with messageID
        try:
            eventToUpdate = self.eventDatabase.findEvent(messageID)
        except Exception:
            await ctx.send("No event found with that message ID")
            return

        # Change time
        eventToUpdate.setTime(newTime)

        # Update event
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)


def setup(bot):
    importlib.reload(event)
    importlib.reload(cfg)
    bot.add_cog(CommandListener(bot))
