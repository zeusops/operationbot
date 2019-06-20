import importlib
import sys
import traceback
from datetime import datetime
from io import StringIO

from discord import Member, Message, NotFound
from discord.ext.commands import (BadArgument, Bot, Context, Converter,
                                  MissingRequiredArgument, command, Cog)

import config as cfg
from event import Event
from eventDatabase import EventDatabase
from secret import COMMAND_CHAR as CMD, ADMINS


class EventDate(Converter):
    async def convert(self, ctx: Context, arg: str) -> datetime:
        try:
            date = datetime.strptime(arg, '%Y-%m-%d')
        except ValueError:
            raise BadArgument("Invalid date format")
        return date.replace(hour=18, minute=45)


class EventTime(Converter):
    async def convert(self, ctx: Context, arg: str) -> datetime:
        try:
            time = datetime.strptime(arg, '%H:%M')
        except ValueError:
            raise BadArgument("Invalid time format")
        return time


class EventMessage(Converter):
    async def convert(self, ctx: Context, arg: str) -> Message:
        try:
            messageid = int(arg)
        except ValueError:
            raise BadArgument("Invalid message ID, needs to be an "
                              "integer")

        # Get channels
        eventchannel = ctx.bot.get_channel(cfg.EVENT_CHANNEL)

        # Get message
        try:
            return await eventchannel.fetch_message(messageid)
        except NotFound:
            raise BadArgument("No message found with that message ID")


class CommandListener(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @command()
    async def exec(self, ctx: Context, flag: str, *, cmd: str):
        """
        Execute arbitrary code.

        If <flag> is p, the result gets wrapped in a print() statement

        Example: exec a variable = 1
        Example: exec p variable
        """
        # Allow only specified admins to send commands for security reasons
        if ctx.message.author.id not in ADMINS:
            await ctx.send("Unauthorized")
            return

        try:
            old_stdout = sys.stdout
            redirected_output = sys.stdout = StringIO()
            if flag == 'p':
                cmd = "print({})".format(cmd)
                exec(cmd)
                msg = "```{}```".format(redirected_output.getvalue())
            else:
                exec(cmd)
                msg = "Executed"
            sys.stdout = old_stdout
        except Exception:
            msg = "An error occured while executing: ```{}```" \
                  .format(traceback.format_exc())
        await ctx.send(msg)

    # Create event command
    @command()
    async def create(self, ctx: Context, date: EventDate):
        """
        Create a new event.

        Example: create 2019-01-01
        """
        eventchannel = self.bot.get_channel(cfg.EVENT_CHANNEL)
        # TODO: Optionally specify sideop -> hide 1PLT and Bravo
        # Create event and sort events, export
        msg, event = await EventDatabase.createEvent(date, eventchannel)
        await EventDatabase.updateReactions(msg, event, self.bot)
        await self.sortEvents(ctx)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send("Created event {} with id {}".format(event, msg.id))

    # Add additional role to event command
    @command()
    async def addrole(self, ctx: Context, eventMessage: EventMessage, *,
                      rolename: str):
        """
        Add a new additional role to the event.

        Example: addrole 530481556083441684 Y1 (Bradley) Driver
        """
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)
        if eventToUpdate is None:
            return

        reaction = eventToUpdate.addAdditionalRole(rolename)
        await EventDatabase.updateEvent(eventMessage, eventToUpdate)
        await eventMessage.add_reaction(reaction)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send("Role added")

    # Remove additional role from event command
    @command()
    async def removerole(self, ctx: Context, eventMessage: EventMessage, *,
                         rolename: str):
        """
        Remove an additional role from the event.

        Example: removerole 530481556083441684 Y1 (Bradley) Driver
        """
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)
        if eventToUpdate is None:
            return

        # Find role
        role = eventToUpdate.findRoleWithName(rolename)
        if role is None:
            await ctx.send("No role found with that name")
            return

        # Remove reactions, remove role, update event, add reactions, export
        for reaction in eventToUpdate.getReactionsOfGroup("Additional"):
            await eventMessage.remove_reaction(reaction, self.bot.user)
        eventToUpdate.removeAdditionalRole(rolename)
        await EventDatabase.updateEvent(eventMessage, eventToUpdate)
        for reaction in eventToUpdate.getReactionsOfGroup("Additional"):
            await eventMessage.add_reaction(reaction)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send("Role removed")

    @command()
    async def removegroup(self, ctx: Context, eventMessage: EventMessage, *,
                          groupName: str):
        """
        Remove a role group from the event.

        Example: removegroup 530481556083441684 Bravo
        """
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)
        if eventToUpdate is None:
            return

        if not eventToUpdate.hasRoleGroup:
            await ctx.send("No role group found with that name")
            return

        # Remove reactions, remove role, update event, add reactions, export
        for reaction in eventToUpdate.getReactionsOfGroup(groupName):
            await eventMessage.remove_reaction(reaction, self.bot.user)
        eventToUpdate.removeRoleGroup(groupName)
        await EventDatabase.updateEvent(eventMessage, eventToUpdate)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send("Group removed")

    # Set title of event command
    @command()
    async def settitle(self, ctx: Context, eventMessage: EventMessage, *,
                       title: str):
        """
        Set event title.

        Example: settitle 530481556083441684 Operation Striker
        """
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)
        if eventToUpdate is None:
            return

        # Change title, update event, export
        # NOTE: Does not check for too long input. Will result in an API error
        # and a bot crash
        eventToUpdate.setTitle(title)
        await EventDatabase.updateEvent(eventMessage, eventToUpdate)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send("Title set")

    # Set date of event command
    @command()
    async def setdate(self, ctx: Context, eventMessage: EventMessage,
                      date: EventDate):
        """
        Set event date.

        Example: setdate 530481556083441684 2019-01-01
        """
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)
        if eventToUpdate is None:
            return

        # Change date
        eventToUpdate.setDate(date)

        # Update event and sort events, export
        await EventDatabase.updateEvent(eventMessage, eventToUpdate)
        await self.sortEvents(ctx)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send("Date set")

    # Set time of event command
    @command()
    async def settime(self, ctx: Context, eventMessage: EventMessage,
                      time: EventTime):
        """
        Set event time.

        Example: settime 530481556083441684 18:45
        """
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)
        if eventToUpdate is None:
            return

        # Change time
        eventToUpdate.setTime(time)

        # Update event and sort events, export
        await EventDatabase.updateEvent(eventMessage, eventToUpdate)
        await self.sortEvents(ctx)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send("Time set")

    # Set terrain of event command
    @command()
    async def setterrain(self, ctx: Context, eventMessage: EventMessage, *,
                         terrain: str):
        """
        Set event terrain.

        Example: settime 530481556083441684 Takistan
        """
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)
        if eventToUpdate is None:
            return

        # Change terrain, update event, export
        eventToUpdate.setTerrain(terrain)
        await EventDatabase.updateEvent(eventMessage, eventToUpdate)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send("Terrain set")

    # Set faction of event command
    @command()
    async def setfaction(self, ctx: Context, eventMessage: EventMessage, *,
                         faction: str):
        """
        Set event faction.

        Example: setfaction 530481556083441684 Insurgents
        """
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)
        if eventToUpdate is None:
            return

        # Change faction, update event, export
        eventToUpdate.setFaction(faction)
        await EventDatabase.updateEvent(eventMessage, eventToUpdate)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send("Faction set")

    # Set faction of event command
    @command()
    async def setdescription(self, ctx: Context, eventMessage: EventMessage, *,
                             description: str):
        """
        Set event description.

        Example: setdescription 530481556083441684 Extra mods required
        """
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)
        if eventToUpdate is None:
            return

        # Change description, update event, export
        eventToUpdate.description = description
        await EventDatabase.updateEvent(eventMessage, eventToUpdate)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send("Description set")

    # Sign user up to event command
    @command()
    async def signup(self, ctx: Context, eventMessage: EventMessage,
                     user: Member, *, roleName: str):
        """
        Sign user up (manually).

        <user> can either be: ID, mention, nickname in quotes, username or username#discriminator
        <roleName> is case-insensitive

        Example: signup 530481556083441684 "S. Gehock" Y1 (Bradley) Gunner
        """  # NOQA
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)
        if eventToUpdate is None:
            return

        # Find role
        role = eventToUpdate.findRoleWithName(roleName)
        if role is None:
            await ctx.send("No role found with that name")
            return

        # Sign user up, update event, export
        eventToUpdate.signup(role, user)
        await EventDatabase.updateEvent(eventMessage, eventToUpdate)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send("User signed up")

    # Remove signup on event of user command
    @command()
    async def removesignup(self, ctx: Context, eventMessage: EventMessage,
                           user: Member):
        """
        Undo user signup (manually).

        <user> can either be: ID, mention, nickname in quotes, username or username#discriminator

        Example: removesignup 530481556083441684 "S. Gehock"
        """  # NOQA
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)
        if eventToUpdate is None:
            return

        # Remove signup, update event, export
        eventToUpdate.undoSignup(user)
        await EventDatabase.updateEvent(eventMessage, eventToUpdate)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send("User signup removed")

    # Archive event command
    @command()
    async def archive(self, ctx: Context, eventMessage: EventMessage):
        """
        Archive event.

        Example: archive 530481556083441684
        """
        eventToUpdate = await self.getEvent(eventMessage.id, ctx)
        if eventToUpdate is None:
            return

        # eventchannel = self.bot.get_channel(cfg.EVENT_CHANNEL)
        eventarchivechannel = self.bot.get_channel(cfg.EVENT_ARCHIVE_CHANNEL)

        # Archive event and export
        await EventDatabase.archiveEvent(eventMessage, eventToUpdate,
                                              eventarchivechannel)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send("Event archived")

    # Delete event command
    @command()
    async def delete(self, ctx: Context, eventMessage: EventMessage):
        """
        Delete event.

        Example: delete 530481556083441684
        """
        # Get message ID
        eventMessageID = eventMessage.id

        # Delete event
        event = EventDatabase.findEvent(eventMessageID)
        if event is not None:
            eventchannel = ctx.bot.get_channel(cfg.EVENT_CHANNEL)
            try:
                eventMessage = await eventchannel.fetch_message(eventMessageID)
            except NotFound:
                await ctx.send("No message found with that message ID")
                return
            await EventDatabase.removeEvent(eventMessage)
            await ctx.send("Removed event from events")
        else:
            event = EventDatabase.findEventInArchive(eventMessageID)
            if event is not None:
                eventMessage = await self.getMessageFromArchive(eventMessageID,
                                                                ctx)
                await EventDatabase.removeEventFromArchive(eventMessage)
                await ctx.send("Removed event from events archive")
            else:
                await ctx.send("No event found with that message ID")

        EventDatabase.toJson()  # Update JSON file

    # sort events command
    @command()
    async def sort(self, ctx: Context):
        """Sort events (manually)."""
        await self.sortEvents(ctx)
        await ctx.send("Events sorted")

    # export to json
    @command()
    async def export(self, ctx: Context):
        """Export event database (manually)."""
        EventDatabase.toJson()
        await ctx.send("EventDatabase exported")

    # import from json
    @command(name="import")
    async def importJson(self, ctx: Context):
        """Import event database (manually)."""
        await EventDatabase.fromJson(self.bot)
        await ctx.send("EventDatabase imported")

    @command()
    async def shutdown(self, ctx: Context):
        """Shut down the bot."""
        await ctx.send("Shutting down")
        print("logging out")
        await self.bot.logout()
        print("exiting")
        sys.exit()

    # TODO: Test commands
    @exec.error
    @create.error
    @addrole.error
    @removerole.error
    @settitle.error
    @settime.error
    @setterrain.error
    @setfaction.error
    @signup.error
    @removesignup.error
    @archive.error
    @delete.error
    @importJson.error
    @export.error
    async def command_error(self, ctx: Context, error):
        if isinstance(error, MissingRequiredArgument):
            await ctx.send("Missing argument. See: {}help {}"
                           .format(CMD, ctx.command))
        elif isinstance(error, BadArgument):
            await ctx.send("Invalid argument: {}. See: {}help {}"
                           .format(error, CMD, ctx.command))
        else:
            await ctx.send("Unexpected error occured: ```{}```".format(error))
            print(error)

    async def getMessageFromArchive(self, messageID: int, ctx: Context):
        """Return a message from the archive based on a message id."""
        # Get channels
        eventarchivechannel = ctx.bot.get_channel(cfg.EVENT_ARCHIVE_CHANNEL)

        # Get message
        try:
            return await eventarchivechannel.fetch_message(messageID)
        except Exception:
            await ctx.send("No message found in archive with that message ID")
            return

    async def getEvent(self, messageID, ctx: Context) -> Event:
        eventToUpdate = EventDatabase.findEvent(messageID)
        if eventToUpdate is None:
            await ctx.send("No event found with that message ID")
            return None
        return eventToUpdate

    async def sortEvents(self, ctx: Context):
        """Sort events in event database"""
        EventDatabase.sortEvents()

        for messageID, event_ in EventDatabase.events.items():
            eventchannel = ctx.bot.get_channel(cfg.EVENT_CHANNEL)
            try:
                eventMessage = await eventchannel.fetch_message(messageID)
            except NotFound:
                await ctx.send("No message found with that message ID")
                return
            await EventDatabase.updateReactions(eventMessage, event_,
                                                     self.bot)
            await EventDatabase.updateEvent(eventMessage, event_)


def setup(bot):
    # importlib.reload(event)
    importlib.reload(cfg)
    bot.add_cog(CommandListener(bot))
