import calendar
import importlib
import sys
import traceback
from datetime import date, datetime, time, timedelta
from io import StringIO
from typing import List
from discord.ext.commands.bot import Bot

import yaml
from discord import Member, Message
from discord.ext.commands import (BadArgument, Cog, Context, Converter,
                                  MissingRequiredArgument, command)
from discord.ext.commands.errors import CommandInvokeError

import config as cfg
import messageFunctions as msgFnc
from errors import (EventNotFound, MessageNotFound, RoleError, RoleNotFound,
                    UnexpectedRole)
from event import Event
from eventDatabase import EventDatabase
from operationbot import OperationBot
from role import Role
from roleGroup import RoleGroup
from secret import ADMINS
from secret import COMMAND_CHAR as CMD
from secret import WW2_DESCRIPTION


class EventDateTime(Converter):
    async def convert(self, ctx: Context, arg: str) -> datetime:
        try:
            date = datetime.strptime(arg, '%Y-%m-%d')
        except ValueError:
            raise BadArgument("Invalid date format {}. Has to be YYYY-MM-DD"
                              .format(arg))
        return date.replace(hour=18, minute=30)


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
        for fmt in('%H:%M', '%H%M'):
            try:
                return datetime.strptime(arg, fmt)
            except ValueError:
                pass
        raise BadArgument("Invalid time format {}. Has to be HH:MM or HHMM"
                          .format(arg))


class EventMessage(Converter):
    async def convert(self, ctx: Context, arg: str) -> Message:
        try:
            eventID = int(arg)
        except ValueError:
            raise BadArgument("Invalid message ID {}, needs to be an "
                              "integer".format(arg))
        try:
            event = EventDatabase.getEventByID(eventID)
            message = await msgFnc.getEventMessage(event, ctx.bot)
        except (EventNotFound, MessageNotFound) as e:
            raise BadArgument(str(e))

        return message


class EventEvent(Converter):
    async def convert(self, ctx: Context, arg: str) -> Event:
        try:
            eventID = int(arg)
        except ValueError:
            raise BadArgument("Invalid message ID {}, needs to be an "
                              "integer".format(arg))

        try:
            event = EventDatabase.getEventByID(eventID)
        except EventNotFound as e:
            raise BadArgument(str(e))

        return event


class ArchivedEvent(Converter):
    async def convert(self, ctx: Context, arg: str) -> Event:
        try:
            eventID = int(arg)
        except ValueError:
            raise BadArgument("Invalid message ID {}, needs to be an "
                              "integer".format(arg))

        try:
            event = EventDatabase.getArchivedEventByID(eventID)
        except EventNotFound as e:
            raise BadArgument(str(e))

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
        except Exception as e:
            await ctx.send("An error occured while reloading: ```py\n{}```"
                           .format(str(e)))
        else:
            await ctx.send("Reloaded {}".format(moduleName))

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
                            batch=False, sideop=False,
                            platoon_size=None, force=False,
                            silent=False) -> Event:
        # TODO: Check for duplicate event dates?
        if date < datetime.today() and not force:
            raise BadArgument("Requested date {} has already passed. "
                              "Use the `force` argument to override"
                              .format(date))

        # Create event and sort events, export
        event: Event = EventDatabase.createEvent(date, ctx.guild.emojis,
                                                 sideop=sideop,
                                                 platoon_size=platoon_size)
        await msgFnc.createEventMessage(event, self.bot.eventchannel)
        if not batch:
            await msgFnc.sortEventMessages(self.bot)
            EventDatabase.toJson()  # Update JSON file
        if not silent:
            await ctx.send("Created event {}".format(event))
        return event

    @command(aliases=["cat"])
    async def show(self, ctx: Context, event: EventEvent):
        await msgFnc.createEventMessage(event, ctx.channel, update_id=False)

    # Create event command
    @command(aliases=['c'])
    async def create(self, ctx: Context, date: EventDateTime, force=None,
                     platoon_size=None):
        """
        Create a new event.

        Use the `force` argument to create past events.

        The platoon_size argument can be used to override the platoon size. Valid values: 1PLT, 2PLT

        Example: create 2019-01-01
                 create 2019-01-01 force
                 create 2019-01-01 force 2PLT
        """  # NOQA

        await self._create_event(ctx, date, platoon_size=platoon_size,
                                 force=force)

    @command(aliases=['cs'])
    async def createside(self, ctx: Context, date: EventDateTime, force=None):
        """
        Create a new side op event.

        Use the `force` argument to create past events.

        Example: createside 2019-01-01
                 createside 2019-01-01 force
        """

        await self._create_event(ctx, date, sideop=True, force=force)

    @command(aliases=['cs2'])
    async def createside2(self, ctx: Context, date: EventDateTime, force=None):
        """
        Create a new WW2 side op event.

        Use the `force` argument to create past events.

        Example: createside2 2019-01-01
                 createside2 2019-01-01 force
        """

        await self._create_event(ctx, date, sideop=True, platoon_size="WW2side", force=force)

    async def _create_side_quick(self, ctx: Context, date: EventDateTime,
                                 terrain: str, faction: str,
                                 zeus: Member = None, time: EventTime = None,
                                 platoon_size: str = None, quiet=False):
        if time is not None:
            date = date.replace(hour=time.hour, minute=time.minute)

        event = await self._create_event(
            ctx, date, sideop=True, platoon_size=platoon_size,
            force=(time is not None), batch=True, silent=True)

        await self._set_quick(ctx, event, terrain, faction, zeus, quiet=True)

        if not quiet:
            await ctx.send("Created event {}".format(event))
        return event

    @command(aliases=['csq'])
    async def createsidequick(self, ctx: Context, date: EventDateTime,
                              terrain: str, faction: str, zeus: Member = None,
                              time: EventTime = None):
        """
        Create and pre-fill a side op event.

        Define the event time to force creation of past events.

        Accepted formats for the optional `time` argument: HH:MM and HHMM. Default time: 18:30

        Example: createsidequick 2019-01-01 Altis USMC Stroker
                 createsidequick 2019-01-01 Altis USMC Stroker 17:30
        """  # NOQA
        await self._create_side_quick(ctx, date, terrain, faction, zeus, time)

    @command(aliases=['csq2'])
    async def createside2quick(self, ctx: Context, date: EventDateTime,
                               terrain: str, faction: str, zeus: Member = None,
                               time: EventTime = None):
        """
        Create and pre-fill a WW2 side op event. Automatically sets description.

        Define the event time to force creation of past events.

        Accepted formats for the optional `time` argument: HH:MM and HHMM. Default time: 18:30

        Example: createside2quick 2019-01-01 Altis USMC Stroker
                 createside2quick 2019-01-01 Altis USMC Stroker 17:30
        """  # NOQA
        event = await self._create_side_quick(ctx, date, terrain, faction, zeus,
                                              time, platoon_size="WW2side")
        if WW2_DESCRIPTION:
            await self._set_description(ctx, event, description=WW2_DESCRIPTION)


    @command(aliases=['mc'])
    async def multicreate(self, ctx: Context, start: EventDate,
                          end: EventDate = None, force=None):
        """Create events for all weekends within specified range.

        If the end date is omitted, events are created for the rest of the
        month. Use the `force` argument to create past events.

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

        event_time = time(hour=18, minute=30)
        with_time = [datetime.combine(day, event_time) for day in days]

        try:
            while True:
                response = await self.bot.wait_for('message', check=pred)
                reply = response.content.lower()

                if reply == 'ok':
                    await ctx.send("Creating events")
                    for day in with_time:
                        await self._create_event(ctx, day, batch=True)
                    await msgFnc.sortEventMessages(self.bot)
                    EventDatabase.toJson()
                    await ctx.send("Done creating events")
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

    @command(aliases=['csz'])
    async def changesize(self, ctx: Context, event: EventEvent,
                         new_size: str):
        if new_size not in cfg.PLATOON_SIZES:
            ctx.send("Invalid new size {}".format(new_size))
            return

        ret = event.changeSize(new_size)
        if ret is None:
            await ctx.send("{}: nothing to be done".format(event))
            return
        if ret.strip() != "":
            await ctx.send(ret)

        await self._update_event(event)
        await ctx.send("Event resized succesfully")

    @command(aliases=['csza'])
    async def changesizeall(self, ctx: Context, new_size: str):
        if new_size not in cfg.PLATOON_SIZES:
            ctx.send("Invalid new size {}".format(new_size))
            return

        for event in EventDatabase.events.values():
            print("converting", event)
            ret = event.changeSize(new_size)
            if ret is None:
                await ctx.send("{}: nothing to be done".format(event))
                continue
            if ret.strip() != "":
                await ctx.send(ret)

            await self._update_event(event, export=False)
            await ctx.send("Event {} resized succesfully".format(event))
        await ctx.send("All events resized succesfully")
        EventDatabase.toJson()

    @command(aliases=['ro'])
    async def reorder(self, ctx: Context, event: EventEvent):
        ret = event.reorder()
        if ret is None:
            await ctx.send("{}: nothing to be done".format(event))
            return
        if ret.strip() != "":
            await ctx.send(ret)

        await self._update_event(event)
        await ctx.send("Event reordered succesfully")

    @command(aliases=['roa'])
    async def resizeall(self, ctx: Context):
        for event in EventDatabase.events.values():
            print("reordering", event)
            ret = event.reorder()
            if ret is None:
                await ctx.send("{}: nothing to be done".format(event))
                continue
            if ret.strip() != "":
                await ctx.send(ret)

            await self._update_event(event, export=False)
            await ctx.send("Event {} reordered succesfully".format(event))
        await ctx.send("All events reordered succesfully")
        EventDatabase.toJson()

    async def _add_role(self, event: Event, rolename: str, batch=False):
        try:
            event.addAdditionalRole(rolename)
        except IndexError:
            user = self.bot.owner
            raise RoleError("Too many additional roles. This should not "
                            "happen. Nag at {}".format(user.mention))
        except RoleError as e:
            if batch:
                # Adding the latest role failed, saving previously added roles
                await self._update_event(event, reorder=False)
            raise RoleError(str(e))
        await self._update_event(event, reorder=False, export=(not batch))

    @command(aliases=['ar'])
    async def addrole(self, ctx: Context, event: EventEvent, *,
                      rolename: str):
        """
        Add a new additional role or multiple roles to the event.

        Separate different roles with a newline

        Example: addrole 1 Y1 (Bradley) Driver

                 addrole 1 Y1 (Bradley) Driver
                   Y1 (Bradley) Gunner
        """
        if '\n' in rolename:
            for role in rolename.split('\n'):
                role = role.strip()
                await self._add_role(event, role, batch=True)
                await ctx.send("Role {} added to event {}".format(role, event))
            await self._update_event(event)
        else:
            await self._add_role(event, rolename)
            await ctx.send("Role {} added to event {}".format(rolename, event))

    # Remove additional role from event command
    @command(aliases=['rr'])
    async def removerole(self, ctx: Context, event: EventEvent, *,
                         rolename: str):
        """
        Remove an additional role from the event.

        Example: removerole 1 Y1 (Bradley) Driver
        """
        event.removeAdditionalRole(rolename)
        await self._update_event(event, reorder=False)
        await ctx.send("Role {} removed from {}".format(rolename, event))

    @command(aliases=['rra'])
    async def removereaction(self, ctx: Context, event: EventEvent,
                             reaction: str):
        """
        Removes a role and the corresponding reaction from the event and updates the message.
        """
        self._find_remove_reaction(reaction, event)
        await self._update_event(event, reorder=False)
        await ctx.send("Reaction {} removed from {}".format(reaction, event))

    def _find_remove_reaction(self, reaction: str, event: Event):
        for group in event.roleGroups.values():
            for role in group.roles:
                if role.name == reaction:
                    group.roles.remove(role)
                    return
        raise BadArgument("No reaction found")

    @command(aliases=['rg'])
    async def removegroup(self, ctx: Context, eventMessage: EventMessage, *,
                          groupName: str):
        """
        Remove a role group from the event.

        Example: removegroup 1 Bravo
        """
        event = EventDatabase.getEventByMessage(eventMessage.id)
        groupName = groupName.strip('"')

        if not event.hasRoleGroup(groupName):
            await ctx.send("No role group found with name {}"
                           .format(groupName))
            return

        # Remove reactions, remove role, update event, add reactions, export
        for reaction in event.getReactionsOfGroup(groupName):
            await eventMessage.remove_reaction(reaction, self.bot.user)
        event.removeRoleGroup(groupName)
        await msgFnc.updateMessageEmbed(eventMessage, event)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send("Group {} removed from {}".format(groupName, event))

    # Set title of event command
    @command(aliases=['stt'])
    async def settitle(self, ctx: Context, event: EventEvent, *,
                       title: str):
        """
        Set event title.

        Example: settitle 1 Operation Striker
        """
        # Change title, update event, export
        # NOTE: Does not check for too long input. Will result in an API error
        # and a bot crash
        event.setTitle(title)
        await self._update_event(event)
        await ctx.send("Title {} set for operation ID {} at {}"
                       .format(event.title, event.id, event.date))

    # Set date of event command
    @command(aliases=['sdt'])
    async def setdate(self, ctx: Context, event: EventEvent,
                      date: EventDateTime):
        """
        Set event date.

        Example: setdate 1 2019-01-01
        """
        # Change date
        event.setDate(date)

        # Update event and sort events, export
        await msgFnc.sortEventMessages(self.bot)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send("Date {} set for operation {} ID {}"
                       .format(event.date, event.title, event.id))

    # Set time of event command
    @command(aliases=['stm'])
    async def settime(self, ctx: Context, event: EventEvent, time: EventTime):
        """
        Set event time.

        Example: settime 1 18:30
        """
        # Change time
        event.setTime(time)

        # Update event and sort events, export
        await msgFnc.sortEventMessages(self.bot)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send("Time set for operation {}"
                       .format(event))

    # Set terrain of event command
    @command(aliases=['st'])
    async def setterrain(self, ctx: Context, event: EventEvent, *,
                         terrain: str):
        """
        Set event terrain.

        Example: settime 1 Takistan
        """
        # Change terrain, update event, export
        event.setTerrain(terrain)
        await self._update_event(event)
        await ctx.send("Terrain {} set for operation {}"
                       .format(event.terrain, event))

    # Set faction of event command
    @command(aliases=['sf'])
    async def setfaction(self, ctx: Context, event: EventEvent, *,
                         faction: str):
        """
        Set event faction.

        Example: setfaction 1 Insurgents
        """
        # Change faction, update event, export
        event.setFaction(faction)
        await self._update_event(event)
        await ctx.send("Faction {} set for operation {}"
                       .format(event.faction, event))

    async def _set_description(self, ctx: Context, event: Event,
                               description: str = ""):
        if description and description[0] == '"' and description[-1] == '"':
            # Strip quotes from description
            description = description[1:-1]

        # Change description, update event
        event.description = description
        await self._update_event(event)
        if description:
            await ctx.send("Description \"{}\" set for operation {}"
                           .format(event.description, event))
        else:
            await ctx.send("Description cleared from operation {}"
                           .format(event))

    @command(aliases=['sd'])
    async def setdescription(self, ctx: Context, event: EventEvent, *,
                             description: str = ""):
        """
        Set or clear event description. To clear the description, run `setdescription [ID]` without the description parameter

        Example: setdescription 1 Extra mods required
        """  # NOQA
        await self._set_description(ctx, event, description)

    @command(aliases=['cld'])
    async def cleardescription(self, ctx: Context, event: EventEvent):
        """
        Clear event description. Alias for `setdescription [ID]`

        Example: cleardescription 1
        """
        await self._set_description(ctx, event)

    @command(aliases=['dbg'])
    async def debugMessage(self, ctx: Context):
        """
        Debug Message. Sends the specified message to discord

        Example: debugMessage
        """
        message = self.bot.signoff_notify_user.mention
        await self.bot.logchannel.send(message)

    async def _set_quick(self, ctx: Context, event: Event, terrain: str,
                         faction: str, zeus: Member = None,
                         time: EventTime = None, quiet=False):
        event.setTerrain(terrain)
        event.setFaction(faction)
        if zeus is not None:
            event.signup(event.findRoleWithName("ZEUS"), zeus)
        if time is not None:
            event.setTime(time)

        await msgFnc.sortEventMessages(self.bot)
        EventDatabase.toJson()  # Update JSON file
        if not quiet:
            await ctx.send("Updated event {}".format(event))

    @command(aliases=['sq'])
    async def setquick(self, ctx: Context, event: EventEvent,
                             terrain: str, faction: str, zeus: Member = None,
                             time: EventTime = None):
        """
        Quickly set event details.

        Accepted formats for the optional `time` argument: HH:MM and HHMM. Default time: 18:30

        Example: setquick 1 Altis USMC
                 setquick 1 Altis USMC Stroker
                 setquick 1 Altis USMC Stroker 17:30
        """  # NOQA
        await self._set_quick(ctx, event, terrain,
                              faction, zeus, time)

    # Sign user up to event command
    @command(aliases=['s'])
    async def signup(self, ctx: Context, event: EventEvent, user: Member, *,
                     roleName: str):
        """
        Sign user up (manually).

        <user> can either be: ID, mention, nickname in quotes, username or username#discriminator
        <roleName> is case-insensitive

        Example: signup 1 "S. Gehock" Y1 (Bradley) Gunner
        """  # NOQA
        # Find role
        role = event.findRoleWithName(roleName)

        # Sign user up, update event, export
        old_signup, replaced_user = event.signup(role, user)
        await self._update_event(event)
        message = "User {} signed up to event {} as {}" \
                 .format(user.display_name, event, role.name)
        if old_signup:
            # User was signed on to a different role previously
            message += ". Signed off from {}".format(old_signup.name)
        if replaced_user.display_name:
            # Took priority over another user's signup
            message += ". Replaced user {}".format(replaced_user.display_name)
        await ctx.send(message)

    # Remove signup on event of user command
    @command(aliases=['rs'])
    async def removesignup(self, ctx: Context, event: EventEvent, user: Member):
        """
        Undo user signup (manually).

        <user> can either be: ID, mention, nickname in quotes, username or username#discriminator

        Example: removesignup 1 "S. Gehock"
        """  # NOQA
        # Remove signup, update event, export
        role: Role = event.undoSignup(user)
        await self._update_event(event)
        await ctx.send("User {} removed from role {} in event {}"
                       .format(user.display_name, role.display_name, event))

    # Archive event command
    @command(aliases=['a'])
    async def archive(self, ctx: Context, event: EventEvent):
        """
        Archive event.

        Example: archive 1
        """

        # Archive event and export
        EventDatabase.archiveEvent(event)
        try:
            eventMessage = await msgFnc.getEventMessage(event, self.bot)
        except MessageNotFound:
            await ctx.send("Internal error: event {} without a message found"
                           .format(event))
        else:
            await eventMessage.delete()

        # Create new message
        await msgFnc.createEventMessage(event, self.bot.eventarchivechannel)

        await ctx.send("Event {} archived".format(event))

    async def _delete(self, event: Event, archived=False):
        # TODO: Move to a more appropriate location
        EventDatabase.removeEvent(event.id, archived=archived)
        try:
            eventMessage = await msgFnc.getEventMessage(
                event, self.bot, archived=archived)
        except MessageNotFound:
            # Message already deleted, nothing to be done
            pass
        else:
            await eventMessage.delete()
        EventDatabase.toJson(archive=archived)

    # Delete event command
    @command(aliases=['d'])
    async def delete(self, ctx: Context, event: EventEvent):
        """
        Delete event.

        Example: delete 1
        """
        await self._delete(event)
        await ctx.send("Event {} removed".format(event))

    @command()
    async def deletearchived(self, ctx: Context, event: ArchivedEvent):
        """
        Delete archived event.

        Example: deletearchived 1
        """
        await self._delete(event, archived=True)
        await ctx.send("Event {} removed from archive".format(event))

    @command(name="list", aliases=["ls"])
    async def listEvents(self, ctx: Context):
        msg = ""
        if not EventDatabase.events:
            await ctx.send("No events in the database")
            return

        for event in EventDatabase.events.values():
            msg += "{}\n".format(event)

        await ctx.send(msg)

    # sort events command
    @command()
    async def sort(self, ctx: Context):
        """Sort events (manually)."""
        await msgFnc.sortEventMessages(self.bot)
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
        # await EventDatabase.fromJson(self.bot)
        await self.bot.import_database()
        await ctx.send("{} events imported".format(len(EventDatabase.events)))

    @command()
    async def dump(self, ctx: Context, event: EventEvent,
                   roleGroup: str = None):
        """Dump given event as YAML for mass editing.

        Use `load` to import the data back in after editing. Specify roleGroup
        to only dump a single group instead of the whole event

        Example: dump 0
        """
        if roleGroup:
            data = event.getRoleGroup(roleGroup).toJson(brief_output=True)
        else:
            data = event.toJson(brief_output=True)

        await ctx.send("```yaml\n{}```"
                       .format(yaml.dump(data, sort_keys=False)))

    @command()
    async def load(self, ctx: Context, event: EventEvent, *, data: str):
        """Load event data as YAML.

        Code tags (`\u200b`\u200b`) are optional. This command can be used to
        remove existing roles and role groups, to change the basic details of
        the operation and to rename additional roles. Note: this command cannot
        create new roles or sign up users to roles, userName is displayed in the
        output of `dump` only for convenience.

        Example: load 0
                 `\u200b`\u200b`yaml
                 name: Additional
                 isInline: false
                 roles:
                 0:
                     name: Role 1
                     userName: ''
                 `\u200b`\u200b`
        """
        # Zero-width spaces (\u200b) above are required in order to prevent
        # Discord formatting from breaking when displaying the autogenerated
        # help messages

        if data.startswith('```') and data.endswith('```'):
            # Remove the first line (containing ```yaml) and the last three
            # characters (containing ```)
            data = data.strip()[3:-3].split('\n', 1)[1].strip()
        data = yaml.safe_load(data)
        if 'roleGroups' in data:
            event.fromJson(event.id, data, ctx.guild.emojis, manual_load=True)
        elif 'roles' in data:
            groupName = data['name']
            roleGroup: RoleGroup = event.getRoleGroup(groupName)
            roleGroup.fromJson(data, ctx.guild.emojis, manual_load=True)
        else:
            raise ValueError("Malformed data")
        await msgFnc.createEventMessage(event, ctx.channel, update_id=False)
        await self._update_event(event)
        await ctx.send("Event imported")

    # @command()
    # async def createmessages(self, ctx: Context):
    #     """Import database and (re)create event messages."""
    #     await self.bot.import_database()
    #     await msgFnc.createMessages(EventDatabase.events, self.bot)
    #     EventDatabase.toJson()
    #     await ctx.send("Event messages created")

    async def _update_event(self, event: Event, import_db=False,
                            reorder=True, export=True):
        # TODO: Move to a more appropriate location
        if import_db:
            await self.bot.import_database()
            # Event instance might have changed because of DB import, get again
            event = EventDatabase.getEventByMessage(event.messageID)

        try:
            message = await msgFnc.getEventMessage(event, self.bot)
        except MessageNotFound:
            message = await msgFnc.createEventMessage(event,
                                                      self.bot.eventchannel)

        await msgFnc.updateMessageEmbed(eventMessage=message,
                                        updatedEvent=event)
        await msgFnc.updateReactions(event=event, message=message,
                                     reorder=reorder)
        if export:
            EventDatabase.toJson()

    @command(aliases=['upde'])
    async def updateevent(self, ctx: Context, event: EventEvent,
                          import_db: bool = False):
        """Import database, update embed and reactions on a single event message."""
        await self._update_event(event, import_db=import_db)
        await ctx.send("Event updated")

    @command(aliases=['syncm'])
    async def syncmessages(self, ctx: Context):
        """Import database, sync messages with events and create missing messages."""
        await self.bot.import_database()
        await msgFnc.syncMessages(EventDatabase.events, self.bot)
        EventDatabase.toJson()
        await ctx.send("Event messages synced")

    @command()
    async def shutdown(self, ctx: Context):
        """Shut down the bot."""
        await ctx.send("Shutting down")
        print("logging out")
        await self.bot.logout()
        print("exiting")
        sys.exit()

    # TODO: Test commands
    @Cog.listener()
    async def on_command_error(self, ctx: Context, error):
        if isinstance(error, MissingRequiredArgument):
            await ctx.send("Missing argument. See: `{}help {}`"
                           .format(CMD, ctx.command))
            return
        elif isinstance(error, BadArgument):
            await ctx.send("Invalid argument: {}. See: `{}help {}`"
                           .format(error, CMD, ctx.command))
            return
        elif isinstance(error, CommandInvokeError):
            if isinstance(error.original, UnexpectedRole):
                await ctx.send("Malformed data: {}. See: `{}help {}`"
                            .format(error.original, CMD, ctx.command))
                return
            elif isinstance(error.original, RoleError):
                await ctx.send("An error occured: ```{}```\n"
                               "Message: `{}`".format(error.original,
                                    ctx.message.clean_content))
                return
            else:
                error = error.original
        print(''.join(traceback.format_exception(type(error),
            error, error.__traceback__)))
        trace = ''.join(traceback.format_exception(type(error), error,
            error.__traceback__, 2))

        message = ctx.message.clean_content.split('\n')
        if len(message) >= 1:
            # Show only first line of the message
            message = "{} [...]".format(message[0])
        else:
            message = message[0]
        msg = "Unexpected error occured: ```{}```\nMessage: " \
                "`{}`\n\n```py\n{}```" \
                .format(error, message, trace)
        if len(msg) >= 2000:
            await ctx.send("Received error message that's over 2000 "
                            "characters, check log.")
            print("Message:", ctx.message.clean_content)
        else:
            await ctx.send(msg)

def setup(bot: Bot):
    # importlib.reload(Event)
    importlib.reload(cfg)
    bot.add_cog(CommandListener(bot))
