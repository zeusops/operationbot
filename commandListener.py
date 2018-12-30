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

    # Add additional role to event command
    @commands.command(pass_context=True, name="signup", brief="")
    async def signup(self, ctx):
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")
        eventMessage = await self.getMessage(info[1], ctx)
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)
        user_ = await self.getUser(info[2], ctx)

        # Get roleName
        roleName = ""
        for word in info[3:]:
            roleName += " " + word

        # Find role
        role_ = eventToUpdate.findRoleWithName(roleName)
        if role_ is None:
            await ctx.send("No role found with that name")
            return

        # Sign user up, update event
        eventToUpdate.signup(role_, user_.display_name)
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)

    # Add additional role to event command
    @commands.command(pass_context=True, name="undosignup", brief="")
    async def undoSignup(self, ctx):
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")
        eventMessage = await self.getMessage(info[1], ctx)
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)
        user_ = await self.getUser(info[2], ctx)

        # Sign user up, update event
        eventToUpdate.undoSignup(user_.display_name)
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)

    # Add additional role to event command
    @commands.command(pass_context=True, name="archive", brief="")
    async def archive(self, ctx):
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")
        eventMessage = await self.getMessage(info[1], ctx)
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)
        eventchannel = self.bot.get_channel(cfg.EVENT_CHANNEL)
        eventarchivechannel = self.bot.get_channel(cfg.EVENT_ARCHIVE_CHANNEL)

        # Archive event
        await self.eventDatabase.archiveEvent(eventMessage, eventToUpdate,
                                              eventchannel,
                                              eventarchivechannel)

    # Delete event command
    @commands.command(pass_context=True, name="delete", brief="")
    async def delete(self, ctx):
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")

        # Get message ID
        eventMessageID = await self.getMessageID(info[1], ctx)

        # Delete event
        event = self.eventDatabase.findEvent(eventMessageID)
        if event is not None:
            eventMessage = await self.getMessage(eventMessageID, ctx)
            await self.eventDatabase.removeEvent(eventMessage)
            await ctx.send("Removed event from events")
        else:
            event = self.eventDatabase.findEventInArchive(eventMessageID)
            if event is not None:
                eventMessage = await self.getMessageFromArchive(eventMessageID,
                                                                ctx)
                await self.eventDatabase.removeEventFromArchive(eventMessage)
                await ctx.send("Removed event from events archive")
            else:
                await ctx.send("No event found with that message ID")

    # Returns message from given string or gives an error
    async def getMessage(self, string, ctx):
        # Get messageID
        messageID = await self.getMessageID(string, ctx)

        # Get channels
        eventchannel = self.bot.get_channel(cfg.EVENT_CHANNEL)

        # Get message
        try:
            return await eventchannel.get_message(messageID)
        except Exception:
            await ctx.send("No message found with that message ID")

    # Returns message from archive from given string or gives an error
    async def getMessageFromArchive(self, string, ctx):
        # Get messageID
        messageID = await self.getMessageID(string, ctx)

        # Get channels
        eventarchivechannel = self.bot.get_channel(cfg.EVENT_ARCHIVE_CHANNEL)

        # Get message
        try:
            return await eventarchivechannel.get_message(messageID)
        except Exception:
            await ctx.send("No message found in archive with that message ID")

    # Returns integer from given string or gives an error
    async def getMessageID(self, string, ctx):
        # Get messageID
        try:
            return int(string)
        except Exception:
            await ctx.send("Invalid message ID, needs to be an integer")
            return

    # Returns event from given message id or gives an error
    async def getEvent(self, messageID, ctx):
        # Find event with messageID
        try:
            return self.eventDatabase.findEvent(messageID)
        except Exception:
            await ctx.send("No event found with that message ID")
            return

    async def getUser(self, string, ctx):
        # Get userID
        try:
            userID = int(string)
        except Exception:
            await ctx.send("Invalid user ID, needs to be an integer")
            return

        # Get user
        for member in ctx.guild.members:
            if member.id == userID:
                return member
        await ctx.send("No user found with that user ID")
        return


def setup(bot):
    importlib.reload(event)
    importlib.reload(cfg)
    bot.add_cog(CommandListener(bot))
