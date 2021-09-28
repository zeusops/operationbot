import calendar
import importlib
import sys
import traceback
from datetime import date, datetime, time, timedelta
from io import StringIO
from typing import List, Optional, Tuple, cast

import yaml
from discord import Member
from discord.channel import TextChannel
from discord.emoji import Emoji
from discord.ext.commands import BadArgument, Cog, Context, command
from discord.ext.commands.errors import (CommandError, CommandInvokeError,
                                         MissingRequiredArgument)

import config as cfg
import messageFunctions as msgFnc
from converters import (ArgArchivedEvent, ArgDate, ArgDateTime, ArgEvent,
                        ArgMessages, ArgRole, ArgTime, UnquotedStr)
from errors import (ExtraMessagesFound, MessageNotFound, RoleError,
                    UnexpectedRole)
from event import Event
from eventDatabase import EventDatabase
from operationbot import OperationBot
from role import Role
from roleGroup import RoleGroup
from secret import ADMINS
from secret import COMMAND_CHAR as CMD
from secret import WW2_MODS


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
            if self.bot.processing:
                await ctx.send("Please wait for the previous operation to "
                               "finish first.")
                return False
            return True

        @bot.check
        async def command_channels_only(ctx: Context):
            """Prevents the bot from being controlled outside of the specified
            command and debug channels."""
            # pylint: disable=protected-access
            return (ctx.channel == self.bot.commandchannel
                    or ctx.channel.id == cfg._test_channel)

    @command(aliases=['t'])
    async def testrole(self, ctx: Context, event: ArgEvent,
                       role: ArgRole):
        """
        Test role parser.

        This command finds and displays roles from the given event. For testing purposes only.
        """  # NOQA
        await ctx.send(f"event {event.id}: {role}")

    @command()
    async def roleparserinfo(self, ctx: Context):
        """
        Display information about parsing roles.
        """

        if ArgRole.__doc__:
            doc = ArgRole.__doc__.split('\n\n')[2]
            await ctx.send(f"How to use commands that use ArgRole for "
                           f"parsing roles: \n\n{doc}")
        else:
            await ctx.send("No documentation found")

    @command()
    async def reloadreload(self, ctx: Context):
        self.bot.unload_extension('reload')
        self.bot.load_extension('reload')
        await ctx.send("Reloaded reload")

    @command()
    async def impreload(self, ctx: Context, moduleName: str):
        # pylint: disable=no-self-use
        try:
            module = importlib.import_module(moduleName)
            importlib.reload(module)
        except ImportError as e:
            await ctx.send(f"Failed to reload module {moduleName}: {str(e)}")
        except Exception as e:  # pylint: disable=broad-except
            await ctx.send("An error occured while reloading: "
                           f"```py\n{str(e)}```")
        else:
            await ctx.send(f"Reloaded {moduleName}")

    @command()
    async def exec(self, ctx: Context, flag: str, *, cmd: str):
        # pylint: disable=no-self-use
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
                cmd = f"print({cmd})"
                exec(cmd)  # pylint: disable=exec-used
                sys.stdout = old_stdout
                msg = f"```py\n{redirected_output.getvalue()}```"
            elif flag == 'c':
                cmd = f"print({cmd})"
                exec(cmd)  # pylint: disable=exec-used
                sys.stdout = old_stdout
                print(f"cmd: {cmd}\noutput: {redirected_output.getvalue()}")
                msg = "Printed in console"
            else:
                exec(cmd)  # pylint: disable=exec-used
                sys.stdout = old_stdout
                msg = "Executed"
            # sys.stdout = old_stdout
        except Exception:  # pylint: disable=broad-except
            msg = ("An error occured while executing: "
                   f"```py\n{traceback.format_exc()}```")
        await ctx.send(msg)

    async def _create_event(self, ctx: Context, _date: datetime,
                            batch=False, sideop=False,
                            platoon_size=None, force=False,
                            silent=False) -> Event:
        # TODO: Check for duplicate event dates?
        if _date < datetime.today() and not force:
            raise BadArgument(f"Requested date {_date} has already passed. "
                              "Use the `force` argument to override")

        # Create event and sort events, export
        event: Event = EventDatabase.createEvent(_date, sideop=sideop,
                                                 platoon_size=platoon_size)
        await msgFnc.get_or_create_messages(event, self.bot.eventchannel)
        if not batch:
            await msgFnc.sortEventMessages(self.bot)
            EventDatabase.toJson()  # Update JSON file
        if not silent:
            await ctx.send(f"Created event {event}")
        return event

    @command(aliases=["cat"])
    async def show(self, ctx: Context, event: ArgEvent):
        message = await msgFnc.getEventMessage(event, self.bot)
        await ctx.send(message.jump_url)
        await msgFnc.get_or_create_messages(event, cast(TextChannel,
                                            ctx.channel), update_id=False)

    # Create event command
    @command(aliases=['c'])
    async def create(self, ctx: Context, _datetime: ArgDateTime, force=None,
                     platoon_size=None):
        """
        Create a new event.

        Use the `force` argument to create past events.

        The platoon_size argument can be used to override the platoon size. Valid values: 1PLT, 2PLT

        Example: create 2019-01-01
                 create 2019-01-01 force
                 create 2019-01-01 force 2PLT
        """  # NOQA

        await self._create_event(ctx, _datetime, platoon_size=platoon_size,
                                 force=force)

    @command(aliases=['cs'])
    async def createside(self, ctx: Context, _datetime: ArgDateTime,
                         force=None):
        """
        Create a new side op event.

        Use the `force` argument to create past events.

        Example: createside 2019-01-01
                 createside 2019-01-01 force
        """

        await self._create_event(ctx, _datetime, sideop=True, force=force)

    @command(aliases=['cs2'])
    async def createside2(self, ctx: Context, _datetime: ArgDateTime,
                          force=None):
        """
        Create a new WW2 side op event.

        Use the `force` argument to create past events.

        Example: createside2 2019-01-01
                 createside2 2019-01-01 force
        """

        await self._create_event(ctx, _datetime, sideop=True,
                                 platoon_size="WW2side", force=force)

    async def _create_quick(
            self, ctx: Context, _datetime: ArgDateTime, terrain: str,
            faction: str, zeus: Member = None, _time: ArgTime = None,
            sideop=False, platoon_size: str = None, quiet=False):
        if _time is not None:
            event_date = _datetime.replace(hour=_time.hour,
                                           minute=_time.minute)

        event = await self._create_event(
            ctx, event_date, sideop=sideop, platoon_size=platoon_size,
            force=(_time is not None), batch=True, silent=True)

        await self._set_quick(ctx, event, terrain, faction, zeus, quiet=True)

        if not quiet:
            await ctx.send(f"Created event {event}")
        return event

    @command(aliases=['cq'])
    async def createquick(
            self, ctx: Context, _datetime: ArgDateTime, terrain: str,
            faction: str, zeus: Member = None, _time: ArgTime = None):
        """
        Create and pre-fill a main op event.

        Define the event time to force creation of past events.

        Accepted formats for the optional `time` argument: HH:MM and HHMM. Default time: 18:30

        Example: createquick 2019-01-01 Altis USMC Stroker
                 createquick 2019-01-01 Altis USMC Stroker 17:30
        """  # NOQA
        await self._create_quick(ctx, _datetime, terrain, faction, zeus, _time,
                                 sideop=False)

    @command(aliases=['csq'])
    async def createsidequick(
            self, ctx: Context, _datetime: ArgDateTime, terrain: str,
            faction: str, zeus: Member = None, _time: ArgTime = None):
        """
        Create and pre-fill a side op event.

        Define the event time to force creation of past events.

        Accepted formats for the optional `time` argument: HH:MM and HHMM. Default time: 18:30

        Example: createsidequick 2019-01-01 Altis USMC Stroker
                 createsidequick 2019-01-01 Altis USMC Stroker 17:30
        """  # NOQA
        await self._create_quick(ctx, _datetime, terrain, faction, zeus, _time,
                                 sideop=True)

    @command(aliases=['csq2'])
    async def createside2quick(
            self, ctx: Context, _datetime: ArgDateTime, terrain: str,
            faction: str, zeus: Member = None, _time: ArgTime = None):
        """
        Create and pre-fill a WW2 side op event. Automatically sets description.

        Define the event time to force creation of past events.

        Accepted formats for the optional `time` argument: HH:MM and HHMM. Default time: 18:30

        Example: createside2quick 2019-01-01 Altis USMC Stroker
                 createside2quick 2019-01-01 Altis USMC Stroker 17:30
        """  # NOQA
        event = await self._create_quick(ctx, _datetime, terrain, faction,
                                         zeus, _time, sideop=True,
                                         platoon_size="WW2side")
        if WW2_MODS:
            await self._set_mods(ctx, event, WW2_MODS)

    @command(aliases=['mc'])
    async def multicreate(self, ctx: Context, start: ArgDate,
                          end: ArgDate = None, force=None):
        """Create events for all weekends within specified range.

        If the end date is omitted, events are created for the rest of the
        month. Use the `force` argument to create past events.

        Example: multicreate 2019-01-01
                 multicreate 2019-01-01 2019-01-15
                 multicreate 2019-01-01 2019-01-10 force
        """
        await self._multi_create(ctx, start, end, force)

    async def _multi_create(self, ctx: Context, start: date,
                            end: date = None, force=None):
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
                f"```{strpastdays}```")
        else:
            strpast = ""

        if len(days) > 0:
            strdays = " ".join([day.isoformat() for day in days])
            message = (
                f"Creating events for following days:\n```{strdays}``` "
                f"{strpast}"
                "Reply with `ok` or `cancel`.")
            await ctx.send(message)
        else:
            message = (
                f"No events to be created.{strpast}"
                "Use the `force` argument to override. "
                f"See `{CMD}help multicreate`")
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
                if reply == 'cancel':
                    await ctx.send("Canceling")
                    self.bot.awaiting_reply = False
                    return
                await ctx.send("Please reply with `ok` or `cancel`.")
        except Exception:  # pylint: disable=broad-except
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')
            self.bot.awaiting_reply = False

    @command(aliases=['csz'])
    async def changesize(self, ctx: Context, event: ArgEvent, new_size: str):
        if new_size not in cfg.PLATOON_SIZES:
            ctx.send(f"Invalid new size {new_size}")
            return

        await self._change_size(ctx, event, new_size)

    async def _change_size(self, ctx: Context, event: Event, new_size: str):
        ret = event.changeSize(new_size)
        if ret is None:
            await ctx.send(f"{event}: nothing to be done")
            return
        if ret.strip() != "":
            await ctx.send(ret)

        await self._update_event(event)
        await ctx.send("Event resized succesfully")

    @command(aliases=['csza'])
    async def changesizeall(self, ctx: Context, new_size: str):
        if new_size not in cfg.PLATOON_SIZES:
            ctx.send(f"Invalid new size {new_size}")
            return

        for event in EventDatabase.events.values():
            print("converting", event)
            await self._change_size(ctx, event, new_size)
        await ctx.send("All events resized succesfully")
        EventDatabase.toJson()

    @command(aliases=['ro'])
    async def reorder(self, ctx: Context, event: ArgEvent):
        ret = event.reorder()
        if ret is None:
            await ctx.send(f"{event}: nothing to be done")
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
                await ctx.send(f"{event}: nothing to be done")
                continue
            if ret.strip() != "":
                await ctx.send(ret)

            await self._update_event(event, export=False)
            await ctx.send(f"Event {event} reordered succesfully")
        await ctx.send("All events reordered succesfully")
        EventDatabase.toJson()

    async def _add_role(self, event: Event, rolename: str, batch=False):
        try:
            event.addAdditionalRole(rolename)
        except IndexError as e:
            user = self.bot.owner
            raise RoleError("Too many additional roles. This should not "
                            f"happen. Nag at {user.mention}") from e
        except RoleError as e:
            if batch:
                # Adding the latest role failed, saving previously added roles
                await self._update_event(event, reorder=False)
            raise e
        if not batch:
            await self._update_event(event, reorder=False)

    @command(aliases=['ar'])
    async def addrole(self, ctx: Context, event: ArgEvent, *,
                      rolename: UnquotedStr):
        """
        Add a new additional role or multiple roles to the event.

        Separate different roles with a newline

        Example: addrole 1 Y1 (Bradley) Driver

                 addrole 1 Y1 (Bradley) Driver
                   Y1 (Bradley) Gunner
        """
        if '\n' in rolename:
            msg = ""
            try:
                for role in rolename.split('\n'):
                    role = role.strip()
                    await self._add_role(event, role, batch=True)
                    msg += f"Role {role} added to event {event}\n"
            except RoleError as e:
                raise e
            else:
                msg += "All roles added, updating events\n"
            finally:
                await ctx.send(msg)
            await self._update_event(event)
            await ctx.send("Events updated")
        else:
            await self._add_role(event, rolename)
            await ctx.send(f"Role {rolename} added to event {event}")

    async def _remove_role(self, ctx: Context, event: ArgEvent, role: ArgRole,
                           check_additional=True):
        role_name = role.name
        event.remove_role(role, check_additional)
        await self._update_event(event, reorder=False)
        await ctx.send(f"Role {role_name} removed from {event}")

    # Remove additional role from event command
    @command(aliases=['rr', 'removeadditionalrole', 'rar'])
    async def removerole(self, ctx: Context, event: ArgEvent, *,
                         role: ArgRole):
        """
        Remove an additional role from the event.

        Example: removerole 1 Y1 (Bradley) Driver
        """
        await self._remove_role(ctx, event, role, check_additional=True)

    @command(aliases=['rmr'])
    async def removemainrole(self, ctx: Context, event: ArgEvent,
                             role: ArgRole):
        """
        Remove a main role from the event.

        Example: removerole 1 B2
        """
        await self._remove_role(ctx, event, role, check_additional=False)

    @command(aliases=['rnr', 'rename'])
    async def renamerole(self, ctx: Context, event: ArgEvent,
                         role: ArgRole, *, new_name: UnquotedStr):
        """
        Rename an additional role of the event.

        Example: renamerole 1 1 "Y2 (Bradley) Driver"
                 rename 1 two "Y2 (Bradley) Driver"
        """
        old_name = role.name
        event.renameAdditionalRole(role, new_name)
        await self._update_event(event, reorder=False)
        await ctx.send(f"Role renamed. Old name: {old_name}, "
                       f"new name: {role} @ {event}")

    @command(aliases=['rra'])
    async def removereaction(self, ctx: Context, event: ArgEvent,
                             role: ArgRole):
        """
        DEPRECATED. Removes a role and the corresponding reaction from the event and updates the message.

        Deprecated: use removemainrole and removerole instead.
        """  # NOQA
        await ctx.send("This command is deprecated. Use `removerole` (`rr`) "
                       "and `removemainrole` (`rmr`) instead.")
        await self._remove_role(ctx, event, role, check_additional=False)

    @command(aliases=['rg'])
    async def removegroup(self, ctx: Context, eventMessages: ArgMessages, *,
                          groupName: UnquotedStr):
        """
        Remove a role group from the event.

        Example: removegroup 1 Bravo
        """
        event = EventDatabase.getEventByMessage(eventMessages[0].id)

        if not event.hasRoleGroup(groupName):
            await ctx.send(f"No role group found with name {groupName}")
            return

        # Remove reactions, remove role, update event, add reactions, export
        event.removeRoleGroup(groupName)
        await msgFnc.updateMessageEmbeds(eventMessages, event,
                                         self.bot.eventchannel)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send(f"Group {groupName} removed from {event}")

    # Set title of event command
    @command(aliases=['stt'])
    async def settitle(self, ctx: Context, event: ArgEvent, *,
                       title: UnquotedStr):
        """
        Set event title.

        Example: settitle 1 Operation Striker
        """
        # Change title, update event, export
        # NOTE: Does not check for too long input. Will result in an API error
        # and a bot crash
        event.setTitle(title)
        await self._update_event(event)
        await ctx.send(f"Title {event.title} set for operation "
                       f"ID {event.id} at {event.date}")

    # Set date of event command
    @command(aliases=['sdt'])
    async def setdate(self, ctx: Context, event: ArgEvent,
                      _datetime: ArgDateTime):
        """
        Set event date.

        Example: setdate 1 2019-01-01
        """
        # Change date
        event.setDate(_datetime)

        # Update event and sort events, export
        await msgFnc.sortEventMessages(self.bot)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send(f"Date {event.date} set for operation "
                       f"{event.title} ID {event.id}")

    # Set time of event command
    @command(aliases=['stm'])
    async def settime(self, ctx: Context, event: ArgEvent,
                      event_time: ArgTime):
        """
        Set event time.

        Example: settime 1 18:30
        """
        # Change time
        event.setTime(event_time)

        # Update event and sort events, export
        await msgFnc.sortEventMessages(self.bot)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send(f"Time set for operation {event}")

    # Set terrain of event command
    @command(aliases=['st'])
    async def setterrain(self, ctx: Context, event: ArgEvent, *,
                         terrain: UnquotedStr):
        """
        Set event terrain.

        Example: setterrain 1 Takistan
        """
        # Change terrain, update event, export
        event.setTerrain(terrain)
        await self._update_event(event)
        await ctx.send(f"Terrain {event.terrain} set for operation {event}")

    # Set faction of event command
    @command(aliases=['sf'])
    async def setfaction(self, ctx: Context, event: ArgEvent, *,
                         faction: UnquotedStr):
        """
        Set event faction.

        Example: setfaction 1 Insurgents
        """
        # Change faction, update event, export
        event.setFaction(faction)
        await self._update_event(event)
        await ctx.send(f"Faction {event.faction} set for operation {event}")

    async def _set_description(self, ctx: Context, event: Event,
                               description: str = ""):
        # Change description, update event
        event.description = description
        await self._update_event(event)
        if description:
            await ctx.send(f"Description \"{event.description}\" "
                           f"set for operation {event}")
        else:
            await ctx.send(f"Description cleared from operation {event}")

    @command(aliases=['sd'])
    async def setdescription(self, ctx: Context, event: ArgEvent, *,
                             description: UnquotedStr = ""):  # type: ignore
        """
        Set or clear event description. To clear the description, run `setdescription [ID]` without the description parameter

        Example: setdescription 1 Extra mods required
        """  # NOQA
        await self._set_description(ctx, event, description)

    @command(aliases=['cld'])
    async def cleardescription(self, ctx: Context, event: ArgEvent):
        """
        Clear event description. Alias for `setdescription [ID]`

        Example: cleardescription 1
        """
        await self._set_description(ctx, event)

    async def _set_port(self, ctx: Context, event: Event,
                        port: int = cfg.PORT_DEFAULT):
        event.port = port
        await self._update_event(event)
        if port != cfg.PORT_DEFAULT:
            await ctx.send(f"Port \"{event.port}\" set for operation {event}")
        else:
            await ctx.send(f"Default port set for operation {event}")

    @command(aliases=['sp'])
    async def setport(self, ctx: Context, event: ArgEvent,
                      port: int = cfg.PORT_DEFAULT):
        """
        Set or clear event server port. To clear the port, run `setport [ID]` without the port parameter

        Example: setport 1 2402
        """  # NOQA
        await self._set_port(ctx, event, port)

    @command(aliases=['clp'])
    async def clearport(self, ctx: Context, event: ArgEvent):
        """
        Clear event port. Alias for `setport [ID]`

        Example: clearport 1
        """
        await self._set_port(ctx, event)

    async def _set_mods(self, ctx: Context, event: Event,
                        mods: str = ""):
        event.mods = mods
        await self._update_event(event)
        if mods:
            await ctx.send(f"Mods ```\n{event.mods}\n``` "
                           f"set for operation {event}")
            await self._set_port(ctx, event, cfg.PORT_MODDED)
        else:
            await ctx.send(f"Mods cleared from operation {event}")
            await self._set_port(ctx, event, cfg.PORT_DEFAULT)

    @command(aliases=['sm', 'setmod'])
    async def setmods(self, ctx: Context, event: ArgEvent,
                      *, mods: UnquotedStr = ""):  # type: ignore
        """
        Set or clear event server mods.

        To clear the mods, run `setmods [ID]` without the mods parameter. Adding mods also sets the server port to the configured sideop port. Removing the mods sets the server port to the default port.

        Example: setmods 1 Custom modset
                 setmods 1 Mod 1
                   Mod 2
                   Mod 3
        """  # NOQA
        await self._set_mods(ctx, event, mods)

    @command(aliases=['clm', 'clearmod'])
    async def clearmods(self, ctx: Context, event: ArgEvent):
        """
        Clear event mods. Alias for `setmods [ID]`

        Example: clearmods 1
        """
        await self._set_mods(ctx, event)

    async def _set_quick(self, ctx: Context, event: Event, terrain: str,
                         faction: str, zeus: Member = None,
                         _time: ArgTime = None, quiet=False):
        event.setTerrain(terrain)
        event.setFaction(faction)
        if zeus is not None:
            event.signup(event.findRoleWithName(cfg.EMOJI_ZEUS), zeus,
                         replace=True)
        if _time is not None:
            event.setTime(_time)

        await msgFnc.sortEventMessages(self.bot)
        EventDatabase.toJson()  # Update JSON file
        if not quiet:
            await ctx.send(f"Updated event {event}")

    @command(aliases=['sq'])
    async def setquick(self, ctx: Context, event: ArgEvent,
                       terrain: str, faction: str, zeus: Member = None,
                       _time: ArgTime = None):
        """
        Quickly set event details.

        Accepted formats for the optional `time` argument: HH:MM and HHMM. Default time: 18:30

        Example: setquick 1 Altis USMC
                 setquick 1 Altis USMC Stroker
                 setquick 1 Altis USMC Stroker 17:30
        """  # NOQA
        await self._set_quick(ctx, event, terrain,
                              faction, zeus, _time)

    # Sign user up to event command
    @command(aliases=['s'])
    async def signup(self, ctx: Context, event: ArgEvent, user: Member, *,
                     role: ArgRole):
        """
        Sign user up to a role.

        Removes user's previous signup from another role and overrides existing signup to the target role, if any.

        <user> can either be: ID, mention, nickname in quotes, username or username#discriminator
        <roleName> is case-insensitive

        Example: signup 1 "S. Gehock" Y1 (Bradley) Gunner
        """  # NOQA
        # Sign user up, update event, export
        old_signup, replaced_user = event.signup(role, user, replace=True)
        await self._update_event(event)
        message = (f"User {user.display_name} signed up to event "
                   f"{event} as {role.name}")
        if old_signup:
            # User was signed on to a different role previously
            message += f". Signed off from {old_signup.name}"
        if replaced_user.display_name:
            # Took priority over another user's signup
            message += f". Replaced user {replaced_user.display_name}"
        await ctx.send(message)

    # Remove signup on event of user command
    @command(aliases=['rs'])
    async def removesignup(self, ctx: Context, event: ArgEvent,
                           user: Member):
        """
        Undo user signup (manually).

        <user> can either be: ID, mention, nickname in quotes, username or username#discriminator

        Example: removesignup 1 "S. Gehock"
        """  # NOQA
        # Remove signup, update event, export
        role: Optional[Role] = event.undoSignup(user)
        if role:
            await self._update_event(event)
            await ctx.send(f"User {user.display_name} removed from role "
                           f"{role.display_name} in event {event}")
        else:
            await ctx.send(f"No signup to remove for user {user.display_name} "
                           f"in event {event}")

    # Archive event command
    @command(aliases=['a'])
    async def archive(self, ctx: Context, event: ArgEvent):
        """
        Archive event.

        Example: archive 1
        """

        # Archive event and export
        EventDatabase.archiveEvent(event)
        try:
            eventMessageList = await msgFnc.getEventMessages(event, self.bot)
        except MessageNotFound:
            await ctx.send(f"Internal error: event {event} without "
                           "a message found")
        else:
            for eventMessage in eventMessageList:
                await eventMessage.delete()

        # Create messages
        await msgFnc.get_or_create_messages(
            event, self.bot.eventarchivechannel)

        await ctx.send(f"Event {event} archived")

    async def _delete(self, event: Event, archived=False):
        # TODO: Move to a more appropriate location
        EventDatabase.removeEvent(event.id, archived=archived)
        try:
            eventMessageList = await msgFnc.getEventMessages(
                event, self.bot, archived=archived)
        except MessageNotFound:
            # Message already deleted, nothing to be done
            pass
        else:
            for eventMessage in eventMessageList:
                await eventMessage.delete()
        EventDatabase.toJson(archive=archived)

    # Delete event command
    @command(aliases=['d'])
    async def delete(self, ctx: Context, event: ArgEvent):
        """
        Delete event.

        Example: delete 1
        """
        await self._delete(event)
        await ctx.send(f"Event {event} removed")

    @command()
    async def deletearchived(self, ctx: Context, event: ArgArchivedEvent):
        """
        Delete archived event.

        Example: deletearchived 1
        """
        await self._delete(event, archived=True)
        await ctx.send(f"Event {event} removed from archive")

    @command(name="list", aliases=["ls"])
    async def listEvents(self, ctx: Context):
        msg = ""
        if not EventDatabase.events:
            await ctx.send("No events in the database")
            return

        for event in EventDatabase.events.values():
            msg += f"{event}\n"

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
        await ctx.send(f"{len(EventDatabase.events)} events imported")

    @command()
    async def dump(self, ctx: Context, event: ArgEvent,
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

        await ctx.send(f"```yaml\n{yaml.dump(data, sort_keys=False)}```")

    @command()
    async def load(self, ctx: Context, event: ArgEvent, *, data: str):
        """Load event data as YAML.

        Code tags (`\u200b`\u200b`) are optional. This command can be used to
        remove existing roles and role groups, to change the basic details of
        the operation and to rename additional roles. Note: this command cannot
        create new roles or sign up users to roles, userName is displayed in
        the output of `dump` only for convenience.

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
        if ctx.guild is None:
            raise CommandError("This command can only be used in a server")
        await self._load(ctx, event, data, ctx.guild.emojis,
                         cast(TextChannel, ctx.channel))
        await ctx.send("Event data loaded")

    async def _load(self, _: Context, event: Event, data: str,
                    emojis: Tuple[Emoji, ...], target: TextChannel = None):
        if data.startswith('```') and data.endswith('```'):
            # Remove the first line (containing ```yaml) and the last three
            # characters (containing ```)
            data = data.strip()[3:-3].split('\n', 1)[1].strip()
        loaded_data = yaml.safe_load(data)
        if 'roleGroups' in loaded_data:
            event.fromJson(event.id, loaded_data, emojis,
                           manual_load=True)
        elif 'roles' in loaded_data:
            groupName = loaded_data['name']
            roleGroup: RoleGroup = event.getRoleGroup(groupName)
            roleGroup.fromJson(loaded_data, emojis, manual_load=True)
        else:
            raise ValueError("Malformed data")
        if target:
            # Display the loaded event in the command channel
            await msgFnc.get_or_create_messages(event, target, update_id=False)
        await self._update_event(event)

    # @command()
    # async def createmessages(self, ctx: Context):
    #     """Import database and (re)create event messages."""
    #     await self.bot.import_database()
    #     await msgFnc.createMessages(EventDatabase.events, self.bot)
    #     EventDatabase.toJson()
    #     await ctx.send("Event messages created")

    async def _update_event(self, event: Event, import_db=False,
                            reorder=True, export=True, exact_number=True):
        # TODO: Move to a more appropriate location
        if import_db:
            await self.bot.import_database()
            # Event instance might have changed because of DB import, get again
            event = EventDatabase.getEventByMessage(event.messageIDList[0])

        try:
            messages = await msgFnc.getEventMessages(event, self.bot,
                                                     exact_number=exact_number)
        except (MessageNotFound, ExtraMessagesFound) as e:
            messages = await msgFnc.get_or_create_messages(
                event, self.bot.eventchannel)
            if isinstance(e, MessageNotFound):
                # New messages were created, we need to reorder the messages
                await msgFnc.sortEventMessages(self.bot)
        else:
            await msgFnc.updateMessageEmbeds(messages, event,
                                             self.bot.eventchannel)
            await msgFnc.updateReactions(event, bot=self.bot, reorder=reorder)

        if export:
            EventDatabase.toJson()

    @command(aliases=['upde'])
    async def updateevent(self, ctx: Context, event: ArgEvent,
                          import_db: bool = False):
        """Import database, update embed and reactions on a single event message."""  # NOQA
        await self._update_event(event, import_db=import_db)
        await ctx.send("Event updated")

    @command(aliases=['syncm'])
    async def syncmessages(self, ctx: Context):
        """Import database, sync messages with events and create missing messages."""  # NOQA
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
    @staticmethod
    async def on_command_error(ctx: Context, error: Exception):
        # pylint: disable=no-else-return
        if isinstance(error, MissingRequiredArgument):
            await ctx.send(f"Missing argument. See: `{CMD}help {ctx.command}`")
            return
        elif isinstance(error, BadArgument):
            await ctx.send(f"Invalid argument: {error}. "
                           f"See: `{CMD}help {ctx.command}`")
            return
        elif isinstance(error, CommandInvokeError):
            if isinstance(error.original, UnexpectedRole):
                await ctx.send(f"Malformed data: {error.original}. "
                               f"See: `{CMD}help {ctx.command}`")
                return
            elif isinstance(error.original, RoleError):
                await ctx.send(f"An error occured: ```{error.original}```\n"
                               f"Message: `{ctx.message.clean_content}`")
                return
            else:
                error = error.original
        print(''.join(traceback.format_exception(type(error),
              error, error.__traceback__)))
        trace = ''.join(traceback.format_exception(type(error), error,
                        error.__traceback__, 2))

        messages = ctx.message.clean_content.split('\n')
        if len(messages) >= 1:
            # Show only first line of the message
            message = f"{messages[0]} [...]"
        else:
            message = messages[0]
        msg = (f"Unexpected error occured: ```{error}```\n"
               f"Message: `{message}`\n\n```py\n{trace}```")
        if len(msg) >= 2000:
            await ctx.send("Received error message that's over 2000 "
                           "characters, check log.")
            print("Message:", ctx.message.clean_content)
        else:
            await ctx.send(msg)


def setup(bot: OperationBot):
    # importlib.reload(Event)
    importlib.reload(cfg)
    bot.add_cog(CommandListener(bot))
