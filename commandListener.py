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
        eventMessage = await self.getMessage(info[1], ctx)
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)

        # Get roleName
        roleName = ""
        for word in info[2:]:
            roleName += " " + word

        # Add role, update event, add reaction
        reaction = eventToUpdate.addAdditionalRole(roleName)
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)
        await self.eventDatabase.addReaction(eventMessage, reaction)

    # Add additional role to event command
    @commands.command(pass_context=True, name="removerole", brief="")
    async def removeRole(self, ctx):
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")
        eventMessage = await self.getMessage(info[1], ctx)
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)

        # Get roleName
        roleName = ""
        for word in info[2:]:
            roleName += " " + word

        # Remove reactions, remove role, update event, add reactions
        for reaction in eventToUpdate.getReactionsOfGroup("Additional"):
            await eventMessage.remove_reaction(reaction, self.bot.user)
        eventToUpdate.removeAdditionalRole(roleName)
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)
        for reaction in eventToUpdate.getReactionsOfGroup("Additional"):
            await self.eventDatabase.addReaction(eventMessage, reaction)

    # Add additional role to event command
    @commands.command(pass_context=True, name="settitle", brief="")
    async def setTitle(self, ctx):
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")
        eventMessage = await self.getMessage(info[1], ctx)
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)

        # Get newTitle
        newTitle = ""
        for word in info[2:]:
            newTitle += " " + word

        # Change title, update event
        eventToUpdate.setTitle(newTitle)
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)

    # Add additional role to event command
    @commands.command(pass_context=True, name="setdate", brief="")
    async def setDate(self, ctx):
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")
        eventMessage = await self.getMessage(info[1], ctx)
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)

        # Get newDate
        newDate = ""
        for word in info[2:]:
            newDate += word

        # Change date, update event
        eventToUpdate.setDate(newDate)
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)

    # Add additional role to event command
    @commands.command(pass_context=True, name="settime", brief="")
    async def setTime(self, ctx):
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")
        eventMessage = await self.getMessage(info[1], ctx)
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)

        # Get newTime
        newTime = ""
        for word in info[2:]:
            newTime += word

        # Change time, update event
        eventToUpdate.setTime(newTime)
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)

    # Add additional role to event command
    @commands.command(pass_context=True, name="setterrain", brief="")
    async def setTerrain(self, ctx):
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")
        eventMessage = await self.getMessage(info[1], ctx)
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)

        # Get newTerrain
        newTerrain = ""
        for word in info[2:]:
            newTerrain += " " + word

        # Change terrain, update event
        eventToUpdate.setTerrain(newTerrain)
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)

    # Add additional role to event command
    @commands.command(pass_context=True, name="setfaction", brief="")
    async def setFaction(self, ctx):
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")
        eventMessage = await self.getMessage(info[1], ctx)
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)

        # Get newFaction
        newFaction = ""
        for word in info[2:]:
            newFaction += " " + word

        # Change faction, update event
        eventToUpdate.setFaction(newFaction)
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)

    # Returns message from given string or gives an error
    async def getMessage(self, string, ctx):
        # Get messageID
        try:
            messageID = int(string)
        except Exception:
            await ctx.send("Invalid message ID, needs to be an integer")
            return

        # Get message
        try:
            eventchannel = self.bot.get_channel(cfg.EVENT_CHANNEL)
            return await eventchannel.get_message(messageID)
        except Exception:
            await ctx.send("No message found with that message ID")
            return

    async def getEvent(self, messageID, ctx):
        # Find event with messageID
        try:
            return self.eventDatabase.findEvent(messageID)
        except Exception:
            await ctx.send("No event found with that message ID")
            return


def setup(bot):
    importlib.reload(event)
    importlib.reload(cfg)
    bot.add_cog(CommandListener(bot))
