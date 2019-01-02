import importlib
import discord
from discord.ext import commands
import event
import config as cfg
from main import eventDatabase_


class CommandListener:

    def __init__(self, bot):
        self.bot = bot
        self.eventDatabase = eventDatabase_

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

        # Create event and sort events, export
        try:
            msg_, event_ = await self.eventDatabase.createEvent(date,
                                                                eventchannel)
        except Exception:
            await ctx.send("Date not properly formatted")
            return
        await self.eventDatabase.updateReactions(msg_, event_, self.bot)
        await self.sortEvents(ctx)
        self.writeJson()  # Update JSON file
        await ctx.send("Created event: {}".format(event_))

    # Add additional role to event command
    @commands.command(pass_context=True, name="addrole", brief="")
    async def addRole(self, ctx):
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")
        if len(info) < 3:
            await ctx.send("Usage: addrole MESSAGEID ROLENAME")
            return
        eventMessage = await self.getMessage(info[1], ctx)
        if eventMessage is None:
            return
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)
        if eventToUpdate is None:
            return

        # Get roleName
        roleName = ""
        for word in info[2:]:
            roleName += " " + word

        # Add role, update event, add reaction, export
        reaction = eventToUpdate.addAdditionalRole(roleName)
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)
        await self.eventDatabase.addReaction(eventMessage, reaction)
        self.writeJson()  # Update JSON file
        await ctx.send("Role added")

    # Remove additional role from event command
    @commands.command(pass_context=True, name="removerole", brief="")
    async def removeRole(self, ctx):
        # TODO: Check for non-existent role
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")
        if len(info) < 3:
            await ctx.send("Usage: removerole MESSAGEID ROLENAME")
            return
        eventMessage = await self.getMessage(info[1], ctx)
        if eventMessage is None:
            return
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)
        if eventToUpdate is None:
            return

        # Get roleName
        roleName = ""
        # TODO: Replace with join()
        for word in info[2:]:
            roleName += " " + word

        # Remove reactions, remove role, update event, add reactions, export
        for reaction in eventToUpdate.getReactionsOfGroup("Additional"):
            await eventMessage.remove_reaction(reaction, self.bot.user)
        eventToUpdate.removeAdditionalRole(roleName)
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)
        for reaction in eventToUpdate.getReactionsOfGroup("Additional"):
            await self.eventDatabase.addReaction(eventMessage, reaction)
        self.writeJson()  # Update JSON file
        await ctx.send("Role removed")

    # Set title of event command
    @commands.command(pass_context=True, name="settitle", brief="")
    async def setTitle(self, ctx):
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")
        if len(info) < 3:
            await ctx.send("Usage: settitle MESSAGEID TITLE")
            return
        eventMessage = await self.getMessage(info[1], ctx)
        if eventMessage is None:
            return
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)
        if eventToUpdate is None:
            return

        # Get newTitle
        newTitle = ""
        for word in info[2:]:
            newTitle += " " + word

        # Change title, update event, export
        # NOTE: Does not check for too long input. Will result in an API error
        # and a bot crash
        eventToUpdate.setTitle(newTitle)
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)
        self.writeJson()  # Update JSON file
        await ctx.send("Title set")

    # Set date of event command
    @commands.command(pass_context=True, name="setdate", brief="")
    async def setDate(self, ctx):
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")
        if len(info) != 3:
            await ctx.send("Usage: setdate MESSAGEID DATE")
            return
        eventMessage = await self.getMessage(info[1], ctx)
        if eventMessage is None:
            return
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)
        if eventToUpdate is None:
            return

        # Get newDateString
        newDateString = ""
        # TODO: Not necessary
        for word in info[2:]:
            newDateString += word

        # Change date
        try:
            eventToUpdate.setDate(newDateString)
        except Exception:
            await ctx.send("Date not properly formatted")
            return

        # Update event and sort events, export
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)
        await self.sortEvents(ctx)
        self.writeJson()  # Update JSON file
        await ctx.send("Date set")

    # Set time of event command
    @commands.command(pass_context=True, name="settime", brief="")
    async def setTime(self, ctx):
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")
        if len(info) != 3:
            await ctx.send("Usage: settime MESSAGEID TIME")
            return
        eventMessage = await self.getMessage(info[1], ctx)
        if eventMessage is None:
            return
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)
        if eventToUpdate is None:
            return

        # Get newTimeString
        # TODO: Check if necessary
        newTimeString = ""
        for word in info[2:]:
            newTimeString += word

        # Change time
        try:
            eventToUpdate.setTime(newTimeString)
        except Exception:
            await ctx.send("Time not properly formatted")
            return

        # Update event and sort events, export
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)
        await self.sortEvents(ctx)
        self.writeJson()  # Update JSON file
        await ctx.send("Time set")

    # Set terrain of event command
    @commands.command(pass_context=True, name="setterrain", brief="")
    async def setTerrain(self, ctx):
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")
        if len(info) < 3:
            await ctx.send("Usage: setterrain MESSAGEID TERRAIN")
            return
        eventMessage = await self.getMessage(info[1], ctx)
        if eventMessage is None:
            return
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)
        if eventToUpdate is None:
            return

        # Get newTerrain
        newTerrain = ""
        for word in info[2:]:
            newTerrain += " " + word

        # Change terrain, update event, export
        eventToUpdate.setTerrain(newTerrain)
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)
        self.writeJson()  # Update JSON file
        await ctx.send("Terrain set")

    # Set faction of event command
    @commands.command(pass_context=True, name="setfaction", brief="")
    async def setFaction(self, ctx):
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")
        if len(info) < 3:
            await ctx.send("Usage: setfaction MESSAGEID FACTION")
            return
        eventMessage = await self.getMessage(info[1], ctx)
        if eventMessage is None:
            return
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)
        if eventToUpdate is None:
            return

        # Get newFaction
        # TODO: join()
        newFaction = ""
        for word in info[2:]:
            newFaction += " " + word

        # Change faction, update event, export
        eventToUpdate.setFaction(newFaction)
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)
        self.writeJson()  # Update JSON file
        await ctx.send("Faction set")

    # Sign user up to event command
    @commands.command(pass_context=True, name="signup", brief="")
    async def signup(self, ctx):
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")
        if len(info) < 4:
            await ctx.send("Usage: signup MESSAGEID USERID ROLENAME")
            return
        eventMessage = await self.getMessage(info[1], ctx)
        if eventMessage is None:
            return
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)
        if eventToUpdate is None:
            return
        user_ = await self.getUser(info[2], ctx)
        if user_ is None:
            return

        # Get roleName
        roleName = ""
        for word in info[3:]:
            roleName += " " + word

        # Find role
        role_ = eventToUpdate.findRoleWithName(roleName)
        if role_ is None:
            await ctx.send("No role found with that name")
            return

        # Sign user up, update event, export
        eventToUpdate.signup(role_, user_)
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)
        self.writeJson()  # Update JSON file
        await ctx.send("User signed up")

    # Remove signup on event of user command
    @commands.command(pass_context=True, name="removesignup", brief="")
    async def removeSignup(self, ctx):
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")
        if len(info) != 3:
            await ctx.send("Usage: removesignup MESSAGEID USERID")
            return
        eventMessage = await self.getMessage(info[1], ctx)
        if eventMessage is None:
            return
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)
        if eventToUpdate is None:
            return
        user_ = await self.getUser(info[2], ctx)

        # Remove signup, update event, export
        eventToUpdate.undoSignup(user_)
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)
        self.writeJson()  # Update JSON file
        await ctx.send("User signup removed")

    # Archive event command
    @commands.command(pass_context=True, name="archive", brief="")
    async def archive(self, ctx):
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")
        if len(info) != 2:
            await ctx.send("Usage: archive MESSAGEID")
            return
        eventMessage = await self.getMessage(info[1], ctx)
        if eventMessage is None:
            return
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)
        if eventToUpdate is None:
            return
        eventchannel = self.bot.get_channel(cfg.EVENT_CHANNEL)
        eventarchivechannel = self.bot.get_channel(cfg.EVENT_ARCHIVE_CHANNEL)

        # Archive event and export
        await self.eventDatabase.archiveEvent(eventMessage, eventToUpdate,
                                              eventchannel,
                                              eventarchivechannel)
        self.writeJson()  # Update JSON file
        await ctx.send("Event archived")

    # Delete event command
    @commands.command(pass_context=True, name="delete", brief="")
    async def delete(self, ctx):
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")
        if len(info) != 2:
            await ctx.send("Usage: delete MESSAGEID")
            return

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

        self.writeJson()  # Update JSON file

    # sort events command
    @commands.command(pass_context=True, name="sort", brief="")
    async def sort(self, ctx):
        await self.sortEvents(ctx)
        await ctx.send("Events sorted")

    # export to json
    @commands.command(pass_context=True, name="export", brief="")
    async def exportJson(self, ctx):
        self.writeJson()
        await ctx.send("EventDatabase exported")

    # import from json
    @commands.command(pass_context=True, name="import", brief="")
    async def importJson(self, ctx):
        await self.readJson()
        await ctx.send("EventDatabase imported")

    # help command
    @commands.command(pass_context=True, name="help", brief="")
    async def help(self, ctx):
        embed = discord.Embed(colour=0xFF4500)
        commandChar = self.bot.command_prefix

        embed.add_field(name="Create event", value=commandChar +
                        "create DATE\n" + commandChar + "create 2019-01-01",
                        inline=False)
        embed.add_field(name="Delete event", value=commandChar +
                        "delete MESSAGEID\n" + commandChar +
                        "delete 439406781123264523", inline=False)
        embed.add_field(name="Archive event", value=commandChar +
                        "archive MESSAGEID\n" + commandChar +
                        "archive 439406781123264523", inline=False)
        embed.add_field(name="Add additional role", value=commandChar +
                        "addrole MESSAGEID ROLENAME\n" + commandChar +
                        "addrole 439406781123264523 Y1 (Bradley) Gunner",
                        inline=False)
        embed.add_field(name="Remove additional role", value=commandChar +
                        "removerole MESSAGEID ROLENAME\n" + commandChar +
                        "removerole 439406781123264523 Y1 (Bradley) Gunner",
                        inline=False)
        embed.add_field(name="Set event title", value=commandChar +
                        "settitle MESSAGEID TITLE\n" + commandChar +
                        "settitle 439406781123264523 Operation Striker",
                        inline=False)
        embed.add_field(name="Set event date", value=commandChar +
                        "setdate MESSAGEID DATE\n" + commandChar +
                        "setdate 439406781123264523 2019-01-01", inline=False)
        embed.add_field(name="Set event time", value=commandChar +
                        "settime MESSAGEID TIME\n" + commandChar +
                        "settime 439406781123264523 18:45", inline=False)
        embed.add_field(name="Set event terrain", value=commandChar +
                        "setterrain MESSAGEID TERRAIN\n" + commandChar +
                        "setterrain 439406781123264523 Takistan", inline=False)
        embed.add_field(name="Set event faction", value=commandChar +
                        "setfaction MESSAGEID FACTION\n" + commandChar +
                        "setfaction 439406781123264523 Insurgents",
                        inline=False)
        embed.add_field(name="Sign user up (manually)", value=commandChar +
                        "signup MESSAGEID USERID ROLENAME\n" + commandChar +
                        "signup 439406781123264523 165853537945780224 Y1 \
                        (Bradley) Gunner", inline=False)
        embed.add_field(name="Undo user signup (manually)", value=commandChar +
                        "removesignup MESSAGEID USERID\n" + commandChar +
                        "removesignup 439406781123264523 165853537945780224",
                        inline=False)
        embed.add_field(name="Import eventDatabase", value=commandChar +
                        "import\n" + commandChar + "import", inline=False)
        embed.add_field(name="Export eventDatabase (manually)",
                        value=commandChar + "export\n" + commandChar +
                        "export", inline=False)
        embed.add_field(name="Sort events (manually)", value=commandChar +
                        "sort\n" + commandChar + "sort", inline=False)

        await ctx.send(embed=embed)

    # Returns message from given string or gives an error
    async def getMessage(self, string, ctx):
        # Get messageID
        messageID = await self.getMessageID(string, ctx)
        if messageID is None:
            return

        # Get channels
        eventchannel = self.bot.get_channel(cfg.EVENT_CHANNEL)

        # Get message
        try:
            return await eventchannel.get_message(messageID)
        except Exception:
            await ctx.send("No message found with that message ID")
            return

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
            return

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

    # Returns user from given string or gives an error
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

    # Sort events in eventDatabase
    async def sortEvents(self, ctx):
        self.eventDatabase.sortEvents()

        for messageID, event_ in self.eventDatabase.events.items():
            eventMessage = await self.getMessage(messageID, ctx)
            await self.eventDatabase.updateReactions(eventMessage, event_,
                                                     self.bot)
            await self.eventDatabase.updateEvent(eventMessage, event_)

    # Export eventDatabase to json
    def writeJson(self):
        self.eventDatabase.toJson()

    # Clear eventchannel and import eventDatabase from json
    async def readJson(self):
        await self.eventDatabase.fromJson(self.bot)


def setup(bot):
    importlib.reload(event)
    importlib.reload(cfg)
    bot.add_cog(CommandListener(bot))
