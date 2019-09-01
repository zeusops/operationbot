import importlib
import sys
import traceback
from datetime import datetime
from io import StringIO

from discord import Member, Message, Forbidden
from discord.ext.commands import (BadArgument, Bot, Cog, Context, Converter,
                                  MissingRequiredArgument, command)

import config as cfg
from event import Event
from eventDatabase import EventDatabase
import messageFunctions as msgFnc
from secret import ADMIN, ADMINS
from secret import COMMAND_CHAR as CMD


class EventDate(Converter):
    async def convert(self, ctx: Context, arg: str) -> datetime:
        try:
            date = datetime.strptime(arg, '%Y-%m-%d')
        except ValueError:
            raise BadArgument("Invalid date format {}. Has to be YYYY-MM-DD"
                              .format(arg))
        return date.replace(hour=18, minute=45)


class EventTime(Converter):
    async def convert(self, ctx: Context, arg: str) -> datetime:
        try:
            time = datetime.strptime(arg, '%H:%M')
        except ValueError:
            raise BadArgument("Invalid time format {}. Has to be HH:MM"
                              .format(arg))
        return time


class EventMessage(Converter):
    async def convert(self, ctx: Context, arg: str) -> Message:
        try:
            eventID = int(arg)
        except ValueError:
            raise BadArgument("Invalid message ID {}, needs to be an "
                              "integer".format(arg))

        event = EventDatabase.getEventByID(eventID)
        if event is None:
            raise BadArgument("No event found with ID {}".format(eventID))
        message = await msgFnc.getEventMessage(ctx.bot, event)
        if message is None:
            raise BadArgument("No message found with event ID {}"
                              .format(eventID))

        return message


class EventEvent(Converter):
    async def convert(self, ctx: Context, arg: str) -> Event:
        try:
            eventID = int(arg)
        except ValueError:
            raise BadArgument("Invalid message ID {}, needs to be an "
                              "integer".format(arg))

        event = EventDatabase.getEventByID(eventID)
        if event is None:
            raise BadArgument("No event found with ID {}".format(eventID))

        return event


class ArchivedEvent(Converter):
    async def convert(self, ctx: Context, arg: str) -> Event:
        try:
            eventID = int(arg)
        except ValueError:
            raise BadArgument("Invalid message ID {}, needs to be an "
                              "integer".format(arg))

        event = EventDatabase.getArchivedEventByID(eventID)
        if event is None:
            raise BadArgument("No event found with ID {}".format(eventID))

        return event


class CommandListener(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @command()
    async def reloadreload(self, ctx: Context):
        self.bot.unload_extension('reload')
        self.bot.load_extension('reload')
        await ctx.send("Reloaded reload")

    @command()
    async def impreload(self, ctx: Context, moduleName: str):
        try:
            module = importlib.import_module(moduleName)
            importlib.reload(module)
        except ImportError as e:
            await ctx.send("Failed to reload module {}: {}"
                           .format(moduleName, str(e)))
        await ctx.send("Reloaded {}".format(moduleName))

    # @command()
    @command()
    async def exec(self, ctx: Context, flag: str, *, cmd: str):
        """
        Execute arbitrary code.

        If <flag> is p, the result gets wrapped in a print() statement
        If <flag> is c, the result gets printed in console

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
                sys.stdout = old_stdout
                msg = "```py\n{}```".format(redirected_output.getvalue())
            elif flag == 'c':
                cmd = "print({})".format(cmd)
                exec(cmd)
                sys.stdout = old_stdout
                print("cmd: {}\noutput: {}".format(
                      cmd, redirected_output.getvalue()))
                msg = "Printed in console"
            else:
                exec(cmd)
                sys.stdout = old_stdout
                msg = "Executed"
            # sys.stdout = old_stdout
        except Exception:
            msg = "An error occured while executing: ```py\n{}```" \
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
        await msgFnc.sortEventMessages(ctx)
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
        event = await msgFnc.getEvent(eventMessage.id, ctx)
        if event is None:
            return

        try:
            reaction = event.addAdditionalRole(rolename)
        except IndexError:
            user = self.bot.get_user(ADMIN)
            await ctx.send("Too many additional roles. This should not "
                           "happen. Nag at {}".format(user.mention))
            return
        try:
            await eventMessage.add_reaction(reaction)
        except Forbidden as e:
            if e.code == 30010:
                await ctx.send("Too many reactions, not adding role {}"
                               .format(rolename))
                event.removeAdditionalRole(rolename)
                return

        await EventDatabase.updateEvent(eventMessage, event)

        EventDatabase.toJson()  # Update JSON file
        await ctx.send("Role {} added to event {}".format(rolename, event))

    # Remove additional role from event command
    @command()
    async def removerole(self, ctx: Context, eventMessage: EventMessage, *,
                         rolename: str):
        """
        Remove an additional role from the event.

        Example: removerole 1 Y1 (Bradley) Driver
        """
        event = await msgFnc.getEvent(eventMessage.id, ctx)
        if event is None:
            return

        # Find role
        role = event.findRoleWithName(rolename)
        if role is None:
            await ctx.send("No role found with name {}".format(rolename))
            return

        # Remove reactions, remove role, update event, add reactions, export
        for reaction in event.getReactionsOfGroup("Additional"):
            await eventMessage.remove_reaction(reaction, self.bot.user)
        event.removeAdditionalRole(rolename)
        await EventDatabase.updateEvent(eventMessage, event)
        for reaction in event.getReactionsOfGroup("Additional"):
            await eventMessage.add_reaction(reaction)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send("Role {} removed from {}".format(rolename, event))

    @command()
    async def removegroup(self, ctx: Context, eventMessage: EventMessage, *,
                          groupName: str):
        """
        Remove a role group from the event.

        Example: removegroup 1 Bravo
        """
        event = await msgFnc.getEvent(eventMessage.id, ctx)
        if event is None:
            return

        if not event.hasRoleGroup:
            await ctx.send("No role group found with name {}"
                           .format(groupName))
            return

        # Remove reactions, remove role, update event, add reactions, export
        for reaction in event.getReactionsOfGroup(groupName):
            await eventMessage.remove_reaction(reaction, self.bot.user)
        event.removeRoleGroup(groupName)
        await EventDatabase.updateEvent(eventMessage, event)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send("Group {} removed from {}".format(groupName, event))

    # Set title of event command
    @command()
    async def settitle(self, ctx: Context, eventMessage: EventMessage, *,
                       title: str):
        """
        Set event title.

        Example: settitle 1 Operation Striker
        """
        event = await msgFnc.getEvent(eventMessage.id, ctx)
        if event is None:
            return

        # Change title, update event, export
        # NOTE: Does not check for too long input. Will result in an API error
        # and a bot crash
        event.setTitle(title)
        await EventDatabase.updateEvent(eventMessage, event)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send("Title {} set for operation ID {} at {}"
                       .format(event.title, event.id, event.date))

    # Set date of event command
    @command()
    async def setdate(self, ctx: Context, eventMessage: EventMessage,
                      date: EventDate):
        """
        Set event date.

        Example: setdate 1 2019-01-01
        """
        event = await msgFnc.getEvent(eventMessage.id, ctx)
        if event is None:
            return

        # Change date
        event.setDate(date)

        # Update event and sort events, export
        await EventDatabase.updateEvent(eventMessage, event)
        await msgFnc.sortEventMessages(ctx)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send("Date {} set for operation {} ID {}"
                       .format(event.date, event.title, event.id))

    # Set time of event command
    @command()
    async def settime(self, ctx: Context, eventMessage: EventMessage,
                      time: EventTime):
        """
        Set event time.

        Example: settime 1 18:45
        """
        event = await msgFnc.getEvent(eventMessage.id, ctx)
        if event is None:
            return

        # Change time
        event.setTime(time)

        # Update event and sort events, export
        await EventDatabase.updateEvent(eventMessage, event)
        await msgFnc.sortEventMessages(ctx)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send("Time set for operation {}"
                       .format(event))

    # Set terrain of event command
    @command()
    async def setterrain(self, ctx: Context, eventMessage: EventMessage, *,
                         terrain: str):
        """
        Set event terrain.

        Example: settime 1 Takistan
        """
        event = await msgFnc.getEvent(eventMessage.id, ctx)
        if event is None:
            return

        # Change terrain, update event, export
        event.setTerrain(terrain)
        await EventDatabase.updateEvent(eventMessage, event)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send("Terrain {} set for operation {}"
                       .format(event.terrain, event))

    # Set faction of event command
    @command()
    async def setfaction(self, ctx: Context, eventMessage: EventMessage, *,
                         faction: str):
        """
        Set event faction.

        Example: setfaction 1 Insurgents
        """
        event = await msgFnc.getEvent(eventMessage.id, ctx)
        if event is None:
            return

        # Change faction, update event, export
        event.setFaction(faction)
        await EventDatabase.updateEvent(eventMessage, event)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send("Faction {} set for operation {}"
                       .format(event.faction, event))

    # Set faction of event command
    @command()
    async def setdescription(self, ctx: Context, eventMessage: EventMessage, *,
                             description: str):
        """
        Set event description.

        Example: setdescription 1 Extra mods required
        """
        event = await msgFnc.getEvent(eventMessage.id, ctx)
        if event is None:
            return

        # Change description, update event, export
        event.description = description
        await EventDatabase.updateEvent(eventMessage, event)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send("Description \"{}\" set for operation {}"
                       .format(event.description, event))

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
        event = await msgFnc.getEvent(eventMessage.id, ctx)
        if event is None:
            return

        # Find role
        role = event.findRoleWithName(roleName)
        if role is None:
            await ctx.send("No role found with name {}".format(roleName))
            return

        # Sign user up, update event, export
        event.signup(role, user)
        await EventDatabase.updateEvent(eventMessage, event)
        EventDatabase.toJson()  # Update JSON file
        # TODO: handle users without separate nickname
        await ctx.send("User {} signed up to event {} as {}"
                       .format(user.nick, event, roleName))

    # Remove signup on event of user command
    @command()
    async def removesignup(self, ctx: Context, eventMessage: EventMessage,
                           user: Member):
        """
        Undo user signup (manually).

        <user> can either be: ID, mention, nickname in quotes, username or username#discriminator

        Example: removesignup 1 "S. Gehock"
        """  # NOQA
        event = await msgFnc.getEvent(eventMessage.id, ctx)
        if event is None:
            return

        # Remove signup, update event, export
        event.undoSignup(user)
        await EventDatabase.updateEvent(eventMessage, event)
        EventDatabase.toJson()  # Update JSON file
        # TODO: handle users without separate nickname
        await ctx.send("User {} removed from event {}"
                       .format(user.nick, event))

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
        eventMessage = await msgFnc.getEventMessage(self.bot, event)
        if eventMessage:
            await eventMessage.delete()
        else:
            await ctx.send("Internal error: event {} without a message found"
                           .format(event))

        # Create new message
        await EventDatabase.createEventMessage(event, eventarchivechannel)

        EventDatabase.toJson()  # Update JSON file
        await ctx.send("Event {} archived".format(event))

    # Delete event command
    @command()
    async def delete(self, ctx: Context, event: EventEvent):
        """
        Delete event.

        Example: delete 1
        """
        eventMessage = await msgFnc.getEventMessage(self.bot, event)
        EventDatabase.removeEvent(event)
        # TODO: handle missing events
        await eventMessage.delete()
        EventDatabase.toJson()
        await ctx.send("Event {} removed".format(event))

    @command()
    async def deletearchived(self, ctx: Context, event: ArchivedEvent):
        """
        Delete archived event.

        Example: deletearchived 1
        """
        eventMessage = await msgFnc.getEventMessage(
            self.bot, event, archived=True)
        EventDatabase.removeEvent(event, archived=True)
        # TODO: handle missing events
        # TODO: Check if archived message can be deleted
        await eventMessage.delete()
        EventDatabase.toJson()
        await ctx.send("Event {} removed from archive".format(event))

    # sort events command
    @command()
    async def sort(self, ctx: Context):
        """Sort events (manually)."""
        await msgFnc.sortEventMessages(ctx)
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
    @removegroup.error
    @settitle.error
    @setdate.error
    @settime.error
    @setterrain.error
    @setfaction.error
    @signup.error
    @removesignup.error
    @archive.error
    @delete.error
    @deletearchived.error
    @sort.error
    @export.error
    @importJson.error
    @shutdown.error
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
