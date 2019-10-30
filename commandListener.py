import calendar
import importlib
import sys
import traceback
from datetime import date, datetime, timedelta, time
from io import StringIO
from typing import List

from discord import Forbidden, Member, Message
from discord.ext.commands import (BadArgument, Cog, Context, Converter,
                                  MissingRequiredArgument, command)

import config as cfg
import messageFunctions as msgFnc
from event import Event
from eventDatabase import EventDatabase
from operationbot import OperationBot
from secret import ADMIN, ADMINS
from secret import COMMAND_CHAR as CMD


class EventDateTime(Converter):
    async def convert(self, ctx: Context, arg: str) -> datetime:
        try:
            date = datetime.strptime(arg, '%Y-%m-%d')
        except ValueError:
            raise BadArgument("Invalid date format {}. Has to be YYYY-MM-DD"
                              .format(arg))
        return date.replace(hour=18, minute=45)


class EventDate(Converter):
    async def convert(self, ctx: Context, arg: str) -> date:
        try:
            _date = date.fromisoformat(arg)
        except ValueError:
            raise BadArgument("Invalid date format {}. Has to be YYYY-MM-DD"
                              .format(arg))
        return _date


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

    def __init__(self, bot: OperationBot):
        self.bot = bot

        @bot.check
        async def globally_block_dms(ctx: Context):
            return ctx.guild is not None

        @bot.check
        async def await_reply(ctx: Context):
            if self.bot.awaiting_reply:
                await ctx.send("Please answer the previous prompt first.")
                return False
            return True

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

    async def _create_event(self, ctx: Context, date: datetime,
                            batch=False):
        # TODO: Optionally specify sideop -> hide 1PLT and Bravo
        # TODO: Check for duplicate event dates?
        # Create event and sort events, export
        msg: Message
        event: Event
        msg, event = await EventDatabase.createEvent(
            date, self.bot.eventchannel)
        if not batch:
            reactions = event.getReactions()
            await EventDatabase.updateReactions(msg, reactions, self.bot.user)
            await msgFnc.sortEventMessages(ctx)
            EventDatabase.toJson()  # Update JSON file
        await ctx.send("Created event {} with id {}".format(event, event.id))

    # Create event command
    @command()
    async def create(self, ctx: Context, date: EventDateTime, force = None):
        """
        Create a new event.

        Use the `force` argument to create past events.

        Example: create 2019-01-01
                 create 2019-01-01 force
        """

        if date < datetime.today() and not force:
            await ctx.send("Requested date {} has already passed. "
                           "Use the `force` argument to override. "
                           "See `{}help create`"
                           .format(date, CMD))
        else:
            await self._create_event(ctx, date)

    @command()
    async def multicreate(self, ctx: Context, start: EventDate,
                          end: EventDate = None, force = None):
        """Create events for all weekends within specified range.

        If the end date is omitted, events are created for the rest of the month.
        Use the `force` argument to create past events.

        Example: multicreate 2019-01-01
                 multicreate 2019-01-01 2019-01-15
                 multicreate 2019-01-01 2019-01-10 force
        """
        if end is None:
            last_day = calendar.monthrange(start.year, start.month)[1]
            end = start.replace(day=last_day)

        delta = end - start
        days: List[date] = []
        past_days: List[date] = []
        weekend = [5, 6, 7]
        day: date
        for i in range(delta.days + 1):
            day = start + timedelta(days=i)
            if day.isoweekday() in weekend:
                if day < date.today() and not force:
                    past_days.append(day)
                else:
                    days.append(day)

        if len(past_days) > 0:
            strpastdays = " ".join([day.isoformat() for day in past_days])
            strpast = (
                "\nFollowing dates are in the past and will be skipped:\n"
                "```{}```".format(strpastdays))
        else:
            strpast = ""

        if len(days) > 0:
            strdays = " ".join([day.isoformat() for day in days])
            message = (
                "Creating events for following days:\n```{}``` "
                "{}"
                "Reply with `ok` or `cancel`."
                .format(strdays, strpast))
            await ctx.send(message)
        else:
            message = (
                "No events to be created.{}"
                "Use the `force` argument to override. "
                "See `{}help multicreate`".format(strpast, CMD))
            await ctx.send(message)
            return

        self.bot.awaiting_reply = True

        def pred(m):
            return m.author == ctx.message.author \
                   and m.channel == ctx.channel

        event_time = time(hour=18, minute=45)
        with_time = [datetime.combine(day, event_time) for day in days]

        try:
            while True:
                response = await self.bot.wait_for('message', check=pred)
                reply = response.content.lower()

                if reply == 'ok':
                    await ctx.send("Creating events")
                    for day in with_time:
                        await self._create_event(ctx, day, batch=True)
                    await msgFnc.sortEventMessages(ctx)
                    EventDatabase.toJson()
                    await ctx.send("{} Done creating events"
                                   .format(ctx.author.mention))
                    self.bot.awaiting_reply = False
                    return
                elif reply == 'cancel':
                    await ctx.send("Canceling")
                    self.bot.awaiting_reply = False
                    return
                else:
                    await ctx.send("Please reply with `ok` or `cancel`.")
        except Exception:
            await ctx.send('```py\n{}\n```'
                           .format(traceback.format_exc()))
            self.bot.awaiting_reply = False

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
            user = self.bot.owner
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
                      date: EventDateTime):
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

        # Archive event and export
        EventDatabase.archiveEvent(event)
        eventMessage = await msgFnc.getEventMessage(self.bot, event)
        if eventMessage:
            await eventMessage.delete()
        else:
            await ctx.send("Internal error: event {} without a message found"
                           .format(event))

        # Create new message
        await EventDatabase.createEventMessage(event,
                                               self.bot.eventarchivechannel)

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
        EventDatabase.removeEvent(event.id)
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
        EventDatabase.removeEvent(event.id, archived=True)
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
    @reloadreload.error
    @impreload.error
    @exec.error
    @create.error
    @multicreate.error
    @addrole.error
    @removerole.error
    @removegroup.error
    @settitle.error
    @setdate.error
    @settime.error
    @setterrain.error
    @setfaction.error
    @setdescription.error
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
            await ctx.send("Missing argument. See: `{}help {}`"
                           .format(CMD, ctx.command))
        elif isinstance(error, BadArgument):
            await ctx.send("Invalid argument: {}. See: `{}help {}`"
                           .format(error, CMD, ctx.command))
        else:
            await ctx.send("Unexpected error occured: ```{}```".format(error))
            print(error)


def setup(bot):
    # importlib.reload(Event)
    importlib.reload(cfg)
    bot.add_cog(CommandListener(bot))
