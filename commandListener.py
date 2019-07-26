import importlib
import sys
import traceback
from datetime import datetime
from io import StringIO

from discord import Member, Message
from discord.ext.commands import (BadArgument, Bot, Cog, Context, Converter,
                                  MissingRequiredArgument, command)

import config as cfg
from event import Event
from eventDatabase import EventDatabase
from messageFunctions import getEvent, getEventMessage, sortEventMessages
from secret import ADMIN, ADMINS
from secret import COMMAND_CHAR as CMD


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
            eventID = int(arg)
        except ValueError:
            raise BadArgument("Invalid message ID, needs to be an "
                              "integer")

        event = EventDatabase.getEventByID(eventID)
        if event is None:
            raise BadArgument("No event found with that ID")
        message = await getEventMessage(ctx.bot, event)
        if message is None:
            raise BadArgument("No message found with that event ID")

        return message


class EventEvent(Converter):
    async def convert(self, ctx: Context, arg: str) -> Event:
        try:
            eventID = int(arg)
        except ValueError:
            raise BadArgument("Invalid message ID, needs to be an "
                              "integer")

        event = EventDatabase.getEventByID(eventID)
        if event is None:
            raise BadArgument("No event found with that ID")

        return event


class ArchivedEvent(Converter):
    async def convert(self, ctx: Context, arg: str) -> Event:
        try:
            eventID = int(arg)
        except ValueError:
            raise BadArgument("Invalid message ID, needs to be an "
                              "integer")

        event = EventDatabase.getArchivedEventByID(eventID)
        if event is None:
            raise BadArgument("No event found with that ID")

        return event


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
        await sortEventMessages(ctx)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send("Created event {} with id {}".format(event, event.id))

    # Add additional role to event command
    @command()
    async def addrole(self, ctx: Context, eventMessage: EventMessage, *,
                      rolename: str):
        """
        Add a new additional role to the event.

        Example: addrole 1 Y1 (Bradley) Driver
        """
        eventToUpdate = await getEvent(eventMessage.id, ctx)
        if eventToUpdate is None:
            return

        try:
            reaction = eventToUpdate.addAdditionalRole(rolename)
        except IndexError:
            user = self.bot.get_user(ADMIN)
            await ctx.send("Too many additional roles. Nag at {}"
                           .format(user.mention))
            return
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

        Example: removerole 1 Y1 (Bradley) Driver
        """
        eventToUpdate = await getEvent(eventMessage.id, ctx)
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

        Example: removegroup 1 Bravo
        """
        eventToUpdate = await getEvent(eventMessage.id, ctx)
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

        Example: settitle 1 Operation Striker
        """
        eventToUpdate = await getEvent(eventMessage.id, ctx)
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

        Example: setdate 1 2019-01-01
        """
        eventToUpdate = await getEvent(eventMessage.id, ctx)
        if eventToUpdate is None:
            return

        # Change date
        eventToUpdate.setDate(date)

        # Update event and sort events, export
        await EventDatabase.updateEvent(eventMessage, eventToUpdate)
        await sortEventMessages(ctx)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send("Date set")

    # Set time of event command
    @command()
    async def settime(self, ctx: Context, eventMessage: EventMessage,
                      time: EventTime):
        """
        Set event time.

        Example: settime 1 18:45
        """
        eventToUpdate = await getEvent(eventMessage.id, ctx)
        if eventToUpdate is None:
            return

        # Change time
        eventToUpdate.setTime(time)

        # Update event and sort events, export
        await EventDatabase.updateEvent(eventMessage, eventToUpdate)
        await sortEventMessages(ctx)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send("Time set")

    # Set terrain of event command
    @command()
    async def setterrain(self, ctx: Context, eventMessage: EventMessage, *,
                         terrain: str):
        """
        Set event terrain.

        Example: settime 1 Takistan
        """
        eventToUpdate = await getEvent(eventMessage.id, ctx)
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

        Example: setfaction 1 Insurgents
        """
        eventToUpdate = await getEvent(eventMessage.id, ctx)
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

        Example: setdescription 1 Extra mods required
        """
        eventToUpdate = await getEvent(eventMessage.id, ctx)
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

        Example: signup 1 "S. Gehock" Y1 (Bradley) Gunner
        """  # NOQA
        eventToUpdate = await getEvent(eventMessage.id, ctx)
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

        Example: removesignup 1 "S. Gehock"
        """  # NOQA
        eventToUpdate = await getEvent(eventMessage.id, ctx)
        if eventToUpdate is None:
            return

        # Remove signup, update event, export
        eventToUpdate.undoSignup(user)
        await EventDatabase.updateEvent(eventMessage, eventToUpdate)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send("User signup removed")

    # Archive event command
    @command()
    async def archive(self, ctx: Context, event: EventEvent):
        """
        Archive event.

        Example: archive 1
        """
        # eventchannel = self.bot.get_channel(cfg.EVENT_CHANNEL)
        eventarchivechannel = self.bot.get_channel(cfg.EVENT_ARCHIVE_CHANNEL)

        # Archive event and export
        EventDatabase.archiveEvent(event)
        eventMessage = await getEventMessage(self.bot, event)
        if eventMessage:
            await eventMessage.delete()
        else:
            ctx.send("Internal error: event without a message found")

        # Create new message
        await EventDatabase.createEventMessage(event, eventarchivechannel)

        EventDatabase.toJson()  # Update JSON file
        await ctx.send("Event archived")

    # Delete event command
    @command()
    async def delete(self, ctx: Context, event: EventEvent):
        """
        Delete event.

        Example: delete 1
        """
        eventMessage = await getEventMessage(self.bot, event)
        EventDatabase.removeEvent(event)
        await ctx.send("Removed event from events")
        # TODO: handle missing events
        await eventMessage.delete()
        EventDatabase.toJson()

    @command()
    async def deletearchived(self, ctx: Context, event: ArchivedEvent):
        """
        Delete archived event.

        Example: deletearchived 1
        """
        eventMessage = await getEventMessage(self.bot, event, archived=True)
        EventDatabase.removeEvent(event, archived=True)
        await ctx.send("Removed event from events")
        # TODO: handle missing events
        await eventMessage.delete()
        EventDatabase.toJson()

    # sort events command
    @command()
    async def sort(self, ctx: Context):
        """Sort events (manually)."""
        await sortEventMessages(ctx)
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


def setup(bot):
    # importlib.reload(event)
    importlib.reload(cfg)
    bot.add_cog(CommandListener(bot))
