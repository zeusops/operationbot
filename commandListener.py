import datetime
import sys
import importlib
import discord
from discord.ext import commands
import event
import config as cfg
from secret import COMMAND_CHAR as CMD
from main import eventDatabase_


class EventDate(commands.Converter):
    async def convert(self, ctx, arg):
        try:
            date = datetime.datetime.strptime(arg, '%Y-%m-%d')
        except ValueError:
            raise commands.BadArgument
        return date.replace(hour=18, minute=45)


class CommandListener:

    def __init__(self, bot):
        self.bot = bot
        self.eventDatabase = eventDatabase_

    # Create event command
    @commands.command(
        help="Create a new event\n"
             "Example: {}create 2019-01-01".format(CMD))
    async def create(self, ctx, date: EventDate):
        eventchannel = self.bot.get_channel(cfg.EVENT_CHANNEL)

        # Create event and sort events, export
        msg_, event_ = await self.eventDatabase.createEvent(date, eventchannel)
        await self.eventDatabase.updateReactions(msg_, event_, self.bot)
        await self.sortEvents(ctx)
        self.writeJson()  # Update JSON file
        await ctx.send("Created event: {}".format(event_))

    @create.error
    async def create_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Missing date. See: {}help create".format(CMD))
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid date")
        else:
            await ctx.send("Unexpected error occured:", error.message)
            print(error)

    # Add additional role to event command
    @commands.command(description="Add a new role to the event")
    async def addrole(self, ctx, messageid: int, *, rolename: str):
        # # Get info from context
        # info = ctx.message.content
        # info = info.split(" ")
        # if len(info) < 3:
        #     await ctx.send("Usage: addrole MESSAGEID ROLENAME")
        #     return
        eventMessage = await self.getMessage(messageid, ctx)
        if eventMessage is None:
            return
        eventToUpdate = await self.getEvent(messageid, ctx)
        if eventToUpdate is None:
            return

        # # Get roleName
        # roleName = " ".join(info[2:])

        # Add role, update event, add reaction, export
        reaction = eventToUpdate.addAdditionalRole(rolename)
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)
        await self.eventDatabase.addReaction(eventMessage, reaction)
        self.writeJson()  # Update JSON file
        await ctx.send("Role added")

    # Remove additional role from event command
    @commands.command()
    async def removerole(self, ctx):
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
        roleName = " ".join(info[2:])

        # Find role
        role_ = eventToUpdate.findRoleWithName(roleName)
        if role_ is None:
            await ctx.send("No role found with that name")
            return

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
    @commands.command()
    async def settitle(self, ctx):
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
        newTitle = " ".join(info[2:])

        # Change title, update event, export
        # NOTE: Does not check for too long input. Will result in an API error
        # and a bot crash
        eventToUpdate.setTitle(newTitle)
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)
        self.writeJson()  # Update JSON file
        await ctx.send("Title set")

    # Set date of event command
    @commands.command()
    async def setdate(self, ctx):
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

        # Change date
        try:
            eventToUpdate.setDate(info[2])
        except Exception:
            await ctx.send("Date not properly formatted")
            return

        # Update event and sort events, export
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)
        await self.sortEvents(ctx)
        self.writeJson()  # Update JSON file
        await ctx.send("Date set")

    # Set time of event command
    @commands.command()
    async def settime(self, ctx):
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

        # Change time
        try:
            eventToUpdate.setTime(info[2])
        except Exception:
            await ctx.send("Time not properly formatted")
            return

        # Update event and sort events, export
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)
        await self.sortEvents(ctx)
        self.writeJson()  # Update JSON file
        await ctx.send("Time set")

    # Set terrain of event command
    @commands.command()
    async def setterrain(self, ctx):
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
        newTerrain = " ".join(info[2:])

        # Change terrain, update event, export
        eventToUpdate.setTerrain(newTerrain)
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)
        self.writeJson()  # Update JSON file
        await ctx.send("Terrain set")

    # Set faction of event command
    @commands.command()
    async def setfaction(self, ctx):
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
        newFaction = " ".join(info[2:])

        # Change faction, update event, export
        eventToUpdate.setFaction(newFaction)
        await self.eventDatabase.updateEvent(eventMessage, eventToUpdate)
        self.writeJson()  # Update JSON file
        await ctx.send("Faction set")

    # Sign user up to event command
    @commands.command()
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
        roleName = " ".join(info[3:])

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
    @commands.command()
    async def removesignup(self, ctx):
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
    @commands.command()
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
    @commands.command()
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
    @commands.command()
    async def sort(self, ctx):
        await self.sortEvents(ctx)
        await ctx.send("Events sorted")

    # export to json
    @commands.command()
    async def export(self, ctx):
        self.writeJson()
        await ctx.send("EventDatabase exported")

    # import from json
    @commands.command(name="import")
    async def importJson(self, ctx):
        await self.readJson()
        await ctx.send("EventDatabase imported")

    @commands.command(brief="Shut down the bot")
    async def shutdown(self, ctx):
        await ctx.send("Shutting down")
        print("logging out")
        await self.bot.logout()
        print("exiting")
        sys.exit()

    # # help command
    # @commands.command(name="help", brief="")
    # async def help(self, ctx):
    #     embed = discord.Embed(colour=0xFF4500)
    #     commandChar = self.bot.command_prefix

    #     embed.add_field(name="Create event", value=commandChar +
    #                     "create DATE\n" + commandChar + "create 2019-01-01",
    #                     inline=False)
    #     embed.add_field(name="Delete event", value=commandChar +
    #                     "delete MESSAGEID\n" + commandChar +
    #                     "delete 439406781123264523", inline=False)
    #     embed.add_field(name="Archive event", value=commandChar +
    #                     "archive MESSAGEID\n" + commandChar +
    #                     "archive 439406781123264523", inline=False)
    #     embed.add_field(name="Add additional role", value=commandChar +
    #                     "addrole MESSAGEID ROLENAME\n" + commandChar +
    #                     "addrole 439406781123264523 Y1 (Bradley) Gunner",
    #                     inline=False)
    #     embed.add_field(name="Remove additional role", value=commandChar +
    #                     "removerole MESSAGEID ROLENAME\n" + commandChar +
    #                     "removerole 439406781123264523 Y1 (Bradley) Gunner",
    #                     inline=False)
    #     embed.add_field(name="Set event title", value=commandChar +
    #                     "settitle MESSAGEID TITLE\n" + commandChar +
    #                     "settitle 439406781123264523 Operation Striker",
    #                     inline=False)
    #     embed.add_field(name="Set event date", value=commandChar +
    #                     "setdate MESSAGEID DATE\n" + commandChar +
    #                     "setdate 439406781123264523 2019-01-01",
    #                     inline=False)
    #     embed.add_field(name="Set event time", value=commandChar +
    #                     "settime MESSAGEID TIME\n" + commandChar +
    #                     "settime 439406781123264523 18:45", inline=False)
    #     embed.add_field(name="Set event terrain", value=commandChar +
    #                     "setterrain MESSAGEID TERRAIN\n" + commandChar +
    #                     "setterrain 439406781123264523 Takistan",
    #                     inline=False)
    #     embed.add_field(name="Set event faction", value=commandChar +
    #                     "setfaction MESSAGEID FACTION\n" + commandChar +
    #                     "setfaction 439406781123264523 Insurgents",
    #                     inline=False)
    #     embed.add_field(name="Sign user up (manually)", value=commandChar +
    #                     "signup MESSAGEID USERID ROLENAME\n" + commandChar +
    #                     "signup 439406781123264523 165853537945780224 Y1 \
    #                     (Bradley) Gunner", inline=False)
    #     embed.add_field(name="Undo user signup (manually)",
    #                     value=commandChar +
    #                     "removesignup MESSAGEID USERID\n" + commandChar +
    #                     "removesignup 439406781123264523 165853537945780224",
    #                     inline=False)
    #     embed.add_field(name="Import eventDatabase", value=commandChar +
    #                     "import\n" + commandChar + "import", inline=False)
    #     embed.add_field(name="Export eventDatabase (manually)",
    #                     value=commandChar + "export\n" + commandChar +
    #                     "export", inline=False)
    #     embed.add_field(name="Sort events (manually)", value=commandChar +
    #                     "sort\n" + commandChar + "sort", inline=False)

    #     await ctx.send(embed=embed)

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
