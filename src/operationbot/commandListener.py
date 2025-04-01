import calendar
import importlib
import logging
import sys
import traceback
from datetime import date, datetime, time, timedelta
from io import StringIO
from typing import Optional, cast

import yaml
from discord import Member
from discord.channel import TextChannel
from discord.emoji import Emoji
from discord.ext.commands import BadArgument, Cog, Context, command
from discord.ext.commands.errors import (
    CommandError,
    CommandInvokeError,
    MissingRequiredArgument,
)

from operationbot import config as cfg
from operationbot import messageFunctions as msgFnc
from operationbot.bot import OperationBot
from operationbot.command_helpers import (
    set_dlc,
    set_overhaul,
    set_reforger,
    show_event,
    update_event,
)
from operationbot.converters import (
    ArgArchivedEvent,
    ArgDate,
    ArgDateTime,
    ArgEvent,
    ArgMember,
    ArgMessage,
    ArgRole,
    ArgTime,
    UnquotedStr,
)
from operationbot.errors import MessageNotFound, RoleError, UnexpectedRole
from operationbot.event import Event
from operationbot.eventDatabase import EventDatabase
from operationbot.roleGroup import RoleGroup
from operationbot.secret import ADMINS, WW2_MODS
from operationbot.secret import COMMAND_CHAR as CMD


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
                await ctx.send(
                    "Please wait for the previous operation to finish first."
                )
                return False
            return True

        @bot.check
        async def command_channels_only(ctx: Context):
            """Limit the bot commands to specific channels.

            Prevents the bot from being controlled outside of the specified
            command and debug channels.
            """
            # pylint: disable=protected-access
            return (
                ctx.channel == self.bot.commandchannel
                or ctx.channel.id == cfg._test_channel
            )

    @command()
    async def testrole(self, ctx: Context, event: ArgEvent, role: ArgRole):
        """
        Test role parser.

        This command finds and displays roles from the given event. For testing purposes only.
        """  # NOQA
        await ctx.send(f"event {event.id}: {role}")

    @command(aliases=["t"])
    async def testmember(self, ctx: Context, member: ArgMember):
        """
        Test role parser.

        This command finds and displays roles from the given event. For testing purposes only.
        """  # NOQA
        await ctx.send(f"member {member}")

    @command()
    async def roleparserinfo(self, ctx: Context):
        """Display information about parsing roles."""
        if ArgRole.__doc__:
            doc = ArgRole.__doc__.split("\n\n")[2]
            await ctx.send(
                f"How to use commands that use ArgRole for parsing roles: \n\n{doc}"
            )
        else:
            await ctx.send("No documentation found")

    @command()
    async def reloadreload(self, ctx: Context):
        self.bot.unload_extension("reload")
        self.bot.load_extension("reload")
        await ctx.send("Reloaded reload")

    @command()
    async def impreload(self, ctx: Context, moduleName: str):
        try:
            module = importlib.import_module(moduleName)
            importlib.reload(module)
        except ImportError as e:
            await ctx.send(f"Failed to reload module {moduleName}: {str(e)}")
        except Exception as e:  # pylint: disable=broad-except
            await ctx.send(f"An error occured while reloading: ```py\n{str(e)}```")
        else:
            await ctx.send(f"Reloaded {moduleName}")

    @command()
    async def exec(self, ctx: Context, flag: str, *, cmd: str):
        """Execute arbitrary code.

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
            if flag == "p":
                cmd = f"print({cmd})"
                exec(cmd)  # pylint: disable=exec-used
                sys.stdout = old_stdout
                msg = f"```py\n{redirected_output.getvalue()}```"
            elif flag == "c":
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
            msg = (
                "An error occured while executing: "
                f"```py\n{traceback.format_exc()}```"
            )
        await ctx.send(msg)

    async def _create_event(
        self,
        ctx: Context,
        _date: datetime,
        batch=False,
        sideop=False,
        platoon_size=None,
        force=False,
        silent=False,
        reforger=False,
    ) -> Event:
        # TODO: Check for duplicate event dates?
        if _date < datetime.today() and not force:
            raise BadArgument(
                f"Requested date {_date} has already passed. "
                "Use the `force` argument to override"
            )

        # Create event and sort events, export
        event: Event = EventDatabase.createEvent(
            _date, sideop=sideop, platoon_size=platoon_size, reforger=reforger
        )
        await msgFnc.createEventMessage(event, self.bot.eventchannel)
        if not batch:
            await msgFnc.sortEventMessages(self.bot)
        if not silent:
            await ctx.send(f"Created event {event}")
            await show_event(ctx, event, self.bot)
        return event

    @command(aliases=["cat"])
    async def show(self, ctx: Context, event: ArgEvent):
        await show_event(ctx, event, self.bot)

    # Create event command
    @command(aliases=["c"])
    async def create(
        self, ctx: Context, _datetime: ArgDateTime, force=False, platoon_size=None
    ):
        """
        Create a new event.

        Use the `force` argument to create past events.

        The platoon_size argument can be used to override the platoon size. Valid values: 1PLT, 2PLT

        Example: create 2019-01-01
                 create 2019-01-01 force
                 create 2019-01-01 force 2PLT
        """  # NOQA

        await self._create_event(ctx, _datetime, platoon_size=platoon_size, force=force)

    @command(aliases=["cs"])
    async def createside(self, ctx: Context, _datetime: ArgDateTime, force=False):
        """Create a new side op event.

        Use the `force` argument to create past events.

        Example: createside 2019-01-01
                 createside 2019-01-01 force
        """
        await self._create_event(ctx, _datetime, sideop=True, force=force)

    @command(aliases=["cr"])
    async def createreforger(
        self, ctx: Context, _datetime: ArgDateTime, force=False, platoon_size=None
    ):
        """
        Create a new Arma Reforger event.

        Use the `force` argument to create past events.

        The platoon_size argument can be used to override the platoon size. Valid values: 1PLT, 2PLT

        Example: createreforger 2019-01-01
                 createreforger 2019-01-01 force
                 createreforger 2019-01-01 force 2PLT
        """  # NOQA

        await self._create_event(
            ctx, _datetime, platoon_size=platoon_size, force=force, reforger=True
        )

    @command(aliases=["crs"])
    async def createreforgerside(
        self, ctx: Context, _datetime: ArgDateTime, force=False
    ):
        """Create a new side op event.

        Use the `force` argument to create past events.

        Example: createreforgerside 2019-01-01
                 createreforgerside 2019-01-01 force
        """
        await self._create_event(
            ctx, _datetime, sideop=True, force=force, reforger=True
        )

    @command(aliases=["cs2"])
    async def createside2(self, ctx: Context, _datetime: ArgDateTime, force=False):
        """Create a new WW2 side op event.

        Use the `force` argument to create past events.

        Example: createside2 2019-01-01
                 createside2 2019-01-01 force
        """
        await self._create_event(
            ctx, _datetime, sideop=True, platoon_size="WW2side", force=force
        )

    async def _create_quick(
        self,
        ctx: Context,
        _datetime: ArgDateTime,
        terrain: str,
        faction: str,
        zeus: Member | None = None,
        _time: ArgTime | None = None,
        sideop=False,
        platoon_size: str | None = None,
        quiet=False,
        reforger=False,
    ):
        if _time is not None:
            _datetime = _datetime.replace(
                hour=_time.hour, minute=_time.minute  # type: ignore
            )

        event = await self._create_event(
            ctx,
            _datetime,
            sideop=sideop,
            platoon_size=platoon_size,
            reforger=reforger,
            force=(_time is not None),
            batch=True,
            silent=True,
        )

        # TODO: Shouldn't create a message and immediately edit
        await self._set_quick(ctx, event, terrain, faction, zeus, quiet=True)

        msg_zeus = f" with Zeus {zeus.display_name}" if zeus else ""
        if not quiet:
            await ctx.send(f"Created event {event}{msg_zeus}")
            await show_event(ctx, event, self.bot)
        return event

    @command(aliases=["cq"])
    async def createquick(
        self,
        ctx: Context,
        _datetime: ArgDateTime,
        terrain: str,
        faction: str,
        zeus: Optional[ArgMember] = None,
        _time: Optional[ArgTime] = None,
    ):
        """
        Create and pre-fill a main op event.

        Define the event time to force creation of past events.

        Accepted formats for the optional `time` argument: HH:MM and HHMM. Default time: 18:30

        Example: createquick 2019-01-01 Altis USMC Stroker
                 createquick 2019-01-01 Altis USMC Stroker 17:30
        """  # NOQA
        await self._create_quick(
            ctx, _datetime, terrain, faction, zeus, _time, sideop=False
        )

    @command(aliases=["csq"])
    async def createsidequick(
        self,
        ctx: Context,
        _datetime: ArgDateTime,
        terrain: str,
        faction: str,
        zeus: Optional[ArgMember] = None,
        _time: Optional[ArgTime] = None,
    ):
        """
        Create and pre-fill a side op event.

        Define the event time to force creation of past events.

        Accepted formats for the optional `time` argument: HH:MM and HHMM. Default time: 18:30

        Example: createsidequick 2019-01-01 Altis USMC Stroker
                 createsidequick 2019-01-01 Altis USMC Stroker 17:30
        """  # NOQA
        await self._create_quick(
            ctx, _datetime, terrain, faction, zeus, _time, sideop=True
        )

    @command(aliases=["crq"])
    async def createreforgerquick(
        self,
        ctx: Context,
        _datetime: ArgDateTime,
        terrain: str,
        faction: str,
        zeus: Optional[ArgMember] = None,
        _time: Optional[ArgTime] = None,
    ):
        """
        Create and pre-fill a Reforger main op event.

        Define the event time to force creation of past events.

        Accepted formats for the optional `time` argument: HH:MM and HHMM. Default time: 18:30

        Example: createreforgerquick 2019-01-01 Altis USMC Stroker
                 createreforgerquick 2019-01-01 Altis USMC Stroker 17:30
        """  # NOQA
        await self._create_quick(
            ctx, _datetime, terrain, faction, zeus, _time, sideop=False, reforger=True
        )

    @command(aliases=["crsq"])
    async def createreforgersidequick(
        self,
        ctx: Context,
        _datetime: ArgDateTime,
        terrain: str,
        faction: str,
        zeus: Optional[ArgMember] = None,
        _time: Optional[ArgTime] = None,
    ):
        """
        Create and pre-fill a Reforger side op event.

        Define the event time to force creation of past events.

        Accepted formats for the optional `time` argument: HH:MM and HHMM. Default time: 18:30

        Example: createreforgersidequick 2019-01-01 Altis USMC Stroker
                 createreforgersidequick 2019-01-01 Altis USMC Stroker 17:30
        """  # NOQA
        await self._create_quick(
            ctx, _datetime, terrain, faction, zeus, _time, sideop=True, reforger=True
        )

    @command(aliases=["csq2"])
    async def createside2quick(
        self,
        ctx: Context,
        _datetime: ArgDateTime,
        terrain: str,
        faction: str,
        zeus: Optional[ArgMember] = None,
        _time: Optional[ArgTime] = None,
    ):
        """
        Create and pre-fill a WW2 side op event. Automatically sets description.

        Define the event time to force creation of past events.

        Accepted formats for the optional `time` argument: HH:MM and HHMM. Default time: 18:30

        Example: createside2quick 2019-01-01 Altis USMC Stroker
                 createside2quick 2019-01-01 Altis USMC Stroker 17:30
        """  # NOQA
        event = await self._create_quick(
            ctx,
            _datetime,
            terrain,
            faction,
            zeus,
            _time,
            sideop=True,
            platoon_size="WW2side",
        )
        if WW2_MODS:
            await self._set_mods(ctx, event, WW2_MODS)

    @command(aliases=["mc"])
    async def multicreate(
        self, ctx: Context, start: ArgDate, end: Optional[ArgDate] = None, force=False
    ):
        """Create events for all weekends within specified range.

        If the end date is omitted, events are created for the rest of the
        month. Use the `force` argument to create past events.

        Example: multicreate 2019-01-01
                 multicreate 2019-01-01 2019-01-15
                 multicreate 2019-01-01 2019-01-10 force
        """
        await self._multi_create(ctx, start, end, force)

    async def _multi_create(
        self, ctx: Context, start: date, end: date | None = None, force=False
    ):
        if end is None:
            last_day = calendar.monthrange(start.year, start.month)[1]
            end = start.replace(day=last_day)

        delta = end - start
        days: list[date] = []
        past_days: list[date] = []
        day: date
        for i in range(delta.days + 1):
            day = start + timedelta(days=i)
            if day.isoweekday() in cfg.MULTICREATE_WEEKEND:
                if day < date.today() and not force:
                    past_days.append(day)
                else:
                    days.append(day)

        if len(past_days) > 0:
            strpastdays = " ".join([day.isoformat() for day in past_days])
            strpast = (
                "\nFollowing dates are in the past and will be skipped:\n"
                f"```{strpastdays}```"
            )
        else:
            strpast = ""

        if len(days) > 0:
            strdays = " ".join([day.isoformat() for day in days])
            message = (
                f"Creating events for following days:\n```{strdays}``` "
                f"{strpast}"
                "Reply with `ok` or `cancel`."
            )
            await ctx.send(message)
        else:
            message = (
                f"No events to be created.{strpast}"
                "Use the `force` argument to override. "
                f"See `{CMD}help multicreate`"
            )
            await ctx.send(message)
            return

        self.bot.awaiting_reply = True

        def pred(m):
            return m.author == ctx.message.author and m.channel == ctx.channel

        event_time = time(hour=18, minute=30)
        with_time = [datetime.combine(day, event_time) for day in days]

        try:
            while True:
                response = await self.bot.wait_for("message", check=pred)
                reply = response.content.lower()

                if reply == "ok":
                    await ctx.send("Creating events")
                    for day in with_time:
                        await self._create_event(ctx, day, batch=True, reforger=True)
                    await msgFnc.sortEventMessages(self.bot)
                    await ctx.send("Done creating events")
                    self.bot.awaiting_reply = False
                    return
                if reply == "cancel":
                    await ctx.send("Canceling")
                    self.bot.awaiting_reply = False
                    return
                await ctx.send("Please reply with `ok` or `cancel`.")
        except Exception:  # pylint: disable=broad-except
            await ctx.send(f"```py\n{traceback.format_exc()}\n```")
            self.bot.awaiting_reply = False

    @command(aliases=["csz"])
    async def changesize(self, ctx: Context, event: ArgEvent, new_size: str):
        if new_size not in cfg.PLATOON_SIZES:
            await ctx.send(f"Invalid new size {new_size}")
            return

        await self._change_size(ctx, event, new_size)

    async def _change_size(self, ctx: Context, event: Event, new_size: str):
        ret = event.changeSize(new_size)
        if ret is None:
            await ctx.send(f"{event}: nothing to be done")
            return
        if ret.strip() != "":
            await ctx.send(ret)

        await update_event(event, self.bot)
        await ctx.send("Event resized succesfully")

    @command(aliases=["csza"])
    async def changesizeall(self, ctx: Context, new_size: str):
        if new_size not in cfg.PLATOON_SIZES:
            await ctx.send(f"Invalid new size {new_size}")
            return

        for event in EventDatabase.events.values():
            print("converting", event)
            await self._change_size(ctx, event, new_size)
        await ctx.send("All events resized succesfully")
        EventDatabase.toJson()

    @command(aliases=["ro"])
    async def reorder(self, ctx: Context, event: ArgEvent):
        ret = event.reorder()
        if ret is None:
            await ctx.send(f"{event}: nothing to be done")
            return
        if ret.strip() != "":
            await ctx.send(ret)

        await update_event(event, self.bot)
        await ctx.send("Event reordered succesfully")

    @command(aliases=["roa"])
    async def resizeall(self, ctx: Context):
        for event in EventDatabase.events.values():
            print("reordering", event)
            ret = event.reorder()
            if ret is None:
                await ctx.send(f"{event}: nothing to be done")
                continue
            if ret.strip() != "":
                await ctx.send(ret)

            await update_event(event, self.bot, export=False)
            await ctx.send(f"Event {event} reordered succesfully")
        await ctx.send("All events reordered succesfully")
        EventDatabase.toJson()

    async def _add_role(self, event: Event, rolename: str, batch=False):
        try:
            event.addAdditionalRole(rolename)
        except IndexError as e:
            user = self.bot.owner
            raise RoleError(
                "Too many additional roles. This should not "
                f"happen. Nag at {user.mention}"
            ) from e
        except RoleError as e:
            if batch:
                # Adding the latest role failed, saving previously added roles
                await update_event(event, self.bot, reorder=False)
            raise e
        await update_event(event, self.bot, reorder=False, export=(not batch))

    @command(aliases=["ar"])
    async def addrole(self, ctx: Context, event: ArgEvent, *, rolename: UnquotedStr):
        """Add a new additional role or multiple roles to the event.

        Separate different roles with a newline

        Example: addrole 1 Y1 (Bradley) Driver

                 addrole 1 Y1 (Bradley) Driver
                   Y1 (Bradley) Gunner
        """
        if "\n" in rolename:
            await ctx.send("Adding roles")
            msg = ""
            try:
                for role in rolename.split("\n"):
                    role = role.strip()
                    await self._add_role(event, role, batch=True)
                    msg += f"Role {role} added to event {event}\n"
            except RoleError as e:
                raise e
            else:
                msg += "All roles added, updating events\n"
            finally:
                await ctx.send(msg)
            await update_event(event, self.bot)
            await ctx.send("Events updated")
        else:
            await self._add_role(event, rolename)
            await ctx.send(f"Role {rolename} added to event {event}")
        await show_event(ctx, event, self.bot)

    # Remove additional role from event command
    @command(aliases=["rr"])
    async def removerole(self, ctx: Context, event: ArgEvent, *, role: ArgRole):
        """Remove an additional role from the event.

        Example: removerole 1 Y1 (Bradley) Driver
        """
        role_name = role.name
        event.removeAdditionalRole(role)
        await update_event(event, self.bot, reorder=False)
        await ctx.send(f"Role {role_name} removed from {event}")
        await show_event(ctx, event, self.bot)

    @command(aliases=["rnr", "rename"])
    async def renamerole(
        self, ctx: Context, event: ArgEvent, role: ArgRole, *, new_name: UnquotedStr
    ):
        """Rename an additional role of the event.

        Example: renamerole 1 1 "Y2 (Bradley) Driver"
                 rename 1 two "Y2 (Bradley) Driver"
        """
        old_name = role.name
        event.renameAdditionalRole(role, new_name)
        await update_event(event, self.bot, reorder=False)
        await ctx.send(
            f"Role renamed. Old name: {old_name}, new name: {role} @ {event}"
        )
        await show_event(ctx, event, self.bot)

    @command(aliases=["rra"])
    async def removereaction(self, ctx: Context, event: ArgEvent, reaction: str):
        """
        Removes a role and the corresponding reaction from the event and updates the message.
        """  # NOQA
        self._find_remove_reaction(reaction, event)
        await update_event(event, self.bot, reorder=False)
        await ctx.send(f"Reaction {reaction} removed from {event}")
        await show_event(ctx, event, self.bot)

    def _find_remove_reaction(self, reaction: str, event: Event):
        for group in event.roleGroups.values():
            for role in group.roles:
                if role.name == reaction:
                    group.roles.remove(role)
                    return
        raise BadArgument("No reaction found")

    @command(aliases=["rg"])
    async def removegroup(
        self, ctx: Context, eventMessage: ArgMessage, *, groupName: UnquotedStr
    ):
        """Remove a role group from the event.

        Example: removegroup 1 Bravo
        """
        event = EventDatabase.getEventByMessage(eventMessage.id)

        if not event.hasRoleGroup(groupName):
            await ctx.send(f"No role group found with name {groupName}")
            return

        # Remove reactions, remove role, update event, add reactions, export
        for reaction in event.getReactionsOfGroup(groupName):
            await eventMessage.remove_reaction(reaction, self.bot.user)
        event.removeRoleGroup(groupName)
        await msgFnc.updateMessageEmbed(eventMessage, event)
        EventDatabase.toJson()  # Update JSON file
        await ctx.send(f"Group {groupName} removed from {event}")
        await show_event(ctx, event, self.bot)

    # Set title of event command
    @command(aliases=["stt"])
    async def settitle(self, ctx: Context, event: ArgEvent, *, title: UnquotedStr):
        """Set event title.

        Example: settitle 1 Operation Striker
        """
        # Change title, update event, export
        # NOTE: Does not check for too long input. Will result in an API error
        # and a bot crash
        event.title = title
        await update_event(event, self.bot)
        await ctx.send(
            f"Title {event.title} set for operation ID {event.id} at {event.date}"
        )
        await show_event(ctx, event, self.bot)

    # Set date of event command
    @command(aliases=["sdt"])
    async def setdate(self, ctx: Context, event: ArgEvent, _datetime: ArgDateTime):
        """Set event date.

        Example: setdate 1 2019-01-01
        """
        # Change date
        event.date = _datetime

        # Update event and sort events, export
        await msgFnc.sortEventMessages(self.bot)
        await ctx.send(
            f"Date {event.date} set for operation {event.title} ID {event.id}"
        )
        await show_event(ctx, event, self.bot)

    # Set time of event command
    @command(aliases=["stm"])
    async def settime(self, ctx: Context, event: ArgEvent, event_time: ArgTime):
        """Set event time.

        Example: settime 1 18:30
        """
        # Change time
        event.time = event_time

        # Update event and sort events, export
        await msgFnc.sortEventMessages(self.bot)
        await ctx.send(f"Time set for operation {event}")
        await show_event(ctx, event, self.bot)

    # Set terrain of event command
    @command(aliases=["st"])
    async def setterrain(self, ctx: Context, event: ArgEvent, *, terrain: UnquotedStr):
        """Set event terrain.

        Example: setterrain 1 Takistan
        """
        # Change terrain, update event, export
        event.terrain = terrain
        await update_event(event, self.bot)
        await ctx.send(f"Terrain {event.terrain} set for operation {event}")
        await show_event(ctx, event, self.bot)

    # Set faction of event command
    @command(aliases=["sf"])
    async def setfaction(self, ctx: Context, event: ArgEvent, *, faction: UnquotedStr):
        """Set event faction.

        Example: setfaction 1 Insurgents
        """
        # Change faction, update event, export
        event.faction = faction
        await update_event(event, self.bot)
        await ctx.send(f"Faction {event.faction} set for operation {event}")
        await show_event(ctx, event, self.bot)

    async def _set_description(self, ctx: Context, event: Event, description: str = ""):
        # Change description, update event
        event.description = description
        await update_event(event, self.bot)
        if description:
            await ctx.send(
                f'Description "{event.description}" ' f"set for operation {event}"
            )
            await show_event(ctx, event, self.bot)
        else:
            await ctx.send(f"Description cleared from operation {event}")

    @command(aliases=["sd"])
    async def setdescription(
        self,
        ctx: Context,
        event: ArgEvent,
        *,
        description: UnquotedStr = UnquotedStr(""),
    ):
        """
        Set or clear event description. To clear the description, run `setdescription [ID]` without the description parameter

        Example: setdescription 1 Extra mods required
        """  # NOQA
        await self._set_description(ctx, event, description)

    @command(aliases=["cld"])
    async def cleardescription(self, ctx: Context, event: ArgEvent):
        """Clear event description. Alias for `setdescription [ID]`

        Example: cleardescription 1
        """
        await self._set_description(ctx, event)

    async def _set_port(self, ctx: Context, event: Event, port: int = cfg.PORT_DEFAULT):
        event.port = port
        await update_event(event, self.bot)
        if port != cfg.PORT_DEFAULT:
            await ctx.send(f'Port "{event.port}" set for operation {event}')
            await show_event(ctx, event, self.bot)
        else:
            await ctx.send(f"Default port set for operation {event}")

    @command(aliases=["sp"])
    async def setport(
        self, ctx: Context, event: ArgEvent, port: int = cfg.PORT_DEFAULT
    ):
        """
        Set or clear event server port. To clear the port, run `setport [ID]` without the port parameter

        Example: setport 1 2402
        """  # NOQA
        await self._set_port(ctx, event, port)

    @command(aliases=["clp"])
    async def clearport(self, ctx: Context, event: ArgEvent):
        """Clear event port. Alias for `setport [ID]`

        Example: clearport 1
        """
        await self._set_port(ctx, event)

    async def _set_mods(self, ctx: Context, event: Event, mods: str = ""):
        event.mods = mods
        await update_event(event, self.bot)
        if mods:
            await ctx.send(f"Mods ```\n{event.mods}\n``` set for operation {event}")
            await self._set_port(ctx, event, cfg.PORT_MODDED)
            await show_event(ctx, event, self.bot)
        else:
            await ctx.send(f"Mods cleared from operation {event}")
            await self._set_port(ctx, event, cfg.PORT_DEFAULT)

    @command(aliases=["sm", "setmod"])
    async def setmods(
        self, ctx: Context, event: ArgEvent, *, mods: UnquotedStr = UnquotedStr("")
    ):
        """
        Set or clear event server mods.

        To clear the mods, run `setmods [ID]` without the mods parameter. Adding mods also sets the server port to the configured sideop port. Removing the mods sets the server port to the default port.

        Example: setmods 1 Custom modset
                 setmods 1 Mod 1
                   Mod 2
                   Mod 3
        """  # NOQA
        await self._set_mods(ctx, event, mods)

    @command(aliases=["clm", "clearmod"])
    async def clearmods(self, ctx: Context, event: ArgEvent):
        """Clear event mods. Alias for `setmods [ID]`

        Example: clearmods 1
        """
        await self._set_mods(ctx, event, "")

    @command(aliases=["sdlc"])
    async def setdlc(self, ctx: Context, event: ArgEvent, *, dlc: UnquotedStr):
        """Set event DLC.

        Example: setdlc 1 APEX
        """
        await set_dlc(ctx, event, self.bot, dlc)

    @command(aliases=["cdlc"])
    async def cleardlc(self, ctx: Context, event: ArgEvent):
        """Clear event DLC.

        Example: cleardlc 1
        """
        await set_dlc(ctx, event, self.bot)

    @command(aliases=["sovh"])
    async def setoverhaul(
        self, ctx: Context, event: ArgEvent, *, overhaul: UnquotedStr
    ):
        """Set event overhaul.

        Example: setoverhaul 1 Vietnam
        """
        await set_overhaul(ctx, event, self.bot, overhaul)

    @command(aliases=["covh"])
    async def clearoverhaul(self, ctx: Context, event: ArgEvent):
        """Clear event overhaul.

        Example: clearoverhaul 1
        """
        await set_overhaul(ctx, event, self.bot)

    @command(aliases=["sr"])
    async def setreforger(self, ctx: Context, event: ArgEvent, reforger: bool):
        """Set or unset Reforger mode for event.

        Example: setreforger 1 true
                 setreforger 1 false
        """
        await set_reforger(ctx, event, self.bot, reforger)

    async def _set_quick(
        self,
        ctx: Context,
        event: Event,
        terrain: str,
        faction: str,
        zeus: Member | None = None,
        _time: ArgTime | None = None,
        quiet=False,
    ):
        event.terrain = terrain
        event.faction = faction
        if zeus is not None:
            event.signup(event.findRoleWithName(cfg.EMOJI_ZEUS), zeus, replace=True)

        message = await msgFnc.getEventMessage(event, self.bot)
        await msgFnc.updateMessageEmbed(message, event)
        EventDatabase.toJson()
        msg_zeus = f" with Zeus {zeus.display_name}" if zeus else ""
        if not quiet:
            await ctx.send(f"Updated event {event}{msg_zeus}")
            await show_event(ctx, event, self.bot)

    @command(aliases=["sq"])
    async def setquick(
        self,
        ctx: Context,
        event: ArgEvent,
        terrain: str,
        faction: str,
        zeus: Optional[ArgMember] = None,
        _time: Optional[ArgTime] = None,
    ):
        """
        Quickly set event details.

        Can't be used to set time for now. Use `settime` after creating the event instead.

        Example: setquick 1 Altis USMC
                 setquick 1 Altis USMC Stroker
        """  # NOQA
        await self._set_quick(ctx, event, terrain, faction, zeus)

    # Sign user up to event command
    @command(aliases=["s"])
    async def signup(
        self,
        ctx: Context,
        event: ArgEvent,
        user: ArgMember,
        *,
        role: Optional[ArgRole] = None,
    ):
        """
        Sign user up to a role.

        Removes user's previous signup from another role and overrides existing signup to the target role, if any.

        <user> can either be: ID, mention, nickname in quotes, username or username#discriminator
        <roleName> is case-insensitive. Defaults to Zeus.

        Example: signup 1 "S. Gehock" Y1 (Bradley) Gunner
                 signup 1 gehock
        """  # NOQA
        if role is None:
            # This is quite an unnecessary cast, but required by mypy unless
            # converters are moved inside their corresponding classes
            role = cast(ArgRole, event.findRoleWithName(cfg.EMOJI_ZEUS))
        # Sign user up, update event, export
        old_signup, replaced_user = event.signup(role, user, replace=True)
        await update_event(event, self.bot)
        message = f"User {user.display_name} signed up to event {event} as {role.name}"
        if old_signup:
            # User was signed on to a different role previously
            message += f". Signed off from {old_signup.name}"
        if replaced_user.display_name:
            # Took priority over another user's signup
            message += f". Replaced user {replaced_user.display_name}"
        await ctx.send(message)
        await show_event(ctx, event, self.bot)

    # Remove signup on event of user command
    @command(aliases=["rs"])
    async def removesignup(self, ctx: Context, event: ArgEvent, user: ArgMember):
        """
        Undo user signup (manually).

        <user> can either be: ID, mention, nickname in quotes, username or username#discriminator

        Example: removesignup 1 "S. Gehock"
        """  # NOQA
        # Remove signup, update event, export
        role = event.undoSignup(user)
        if role is None:
            await ctx.send(
                f"No signup to remove for user {user.display_name} in event {event}"
            )
            return

        await update_event(event, self.bot)
        await ctx.send(
            f"User {user.display_name} removed from role "
            f"{role.display_name} in event {event}"
        )
        await show_event(ctx, event, self.bot)

    # Archive event command
    @command(aliases=["a"])
    async def archive(self, ctx: Context, event: ArgEvent):
        """Archive event.

        Example: archive 1
        """
        await msgFnc.archive_single_event(event, ctx, self.bot)
        await ctx.send(f"Event {event} archived")

    @command(aliases=["ap"])
    async def archivepast(self, ctx: Context):
        """Archive all past events.

        Example: archivepast
        """
        archived = await msgFnc.archive_past_events(self.bot, target=ctx)
        if not archived:
            await ctx.send("No events to archive")

    async def _delete(self, event: Event, archived=False):
        # TODO: Move to a more appropriate location
        EventDatabase.removeEvent(event.id, archived=archived)
        try:
            eventMessage = await msgFnc.getEventMessage(
                event, self.bot, archived=archived
            )
        except MessageNotFound:
            # Message already deleted, nothing to be done
            pass
        else:
            await eventMessage.delete()
        EventDatabase.toJson(archive=archived)

    # Delete event command
    @command(aliases=["d"])
    async def delete(self, ctx: Context, event: ArgEvent):
        """Delete event.

        Example: delete 1
        """
        await self._delete(event)
        await ctx.send(f"Event {event} removed")

    @command()
    async def deletearchived(self, ctx: Context, event: ArgArchivedEvent):
        """Delete archived event.

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
    async def dump(
        self, ctx: Context, event: ArgEvent, roleGroup: Optional[str] = None
    ):
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
        await self._load(
            ctx, event, data, ctx.guild.emojis, cast(TextChannel, ctx.channel)
        )
        await ctx.send("Event data loaded")

    async def _load(
        self,
        _: Context,
        event: Event,
        data: str,
        emojis: tuple[Emoji, ...],
        target: TextChannel | None = None,
    ):
        if data.startswith("```") and data.endswith("```"):
            # Remove the first line (containing ```yaml) and the last three
            # characters (containing ```)
            data = data.strip()[3:-3].split("\n", 1)[1].strip()
        loaded_data = yaml.safe_load(data)
        if "roleGroups" in loaded_data:
            event.fromJson(event.id, loaded_data, emojis, manual_load=True)
        elif "roles" in loaded_data:
            groupName = loaded_data["name"]
            roleGroup: RoleGroup = event.getRoleGroup(groupName)
            roleGroup.fromJson(loaded_data, emojis, manual_load=True)
        else:
            raise ValueError("Malformed data")
        if target:
            # Display the loaded event in the command channel
            await msgFnc.createEventMessage(event, target, update_id=False)
        await update_event(event, self.bot)

    # @command()
    # async def createmessages(self, ctx: Context):
    #     """Import database and (re)create event messages."""
    #     await self.bot.import_database()
    #     await msgFnc.createMessages(EventDatabase.events, self.bot)
    #     EventDatabase.toJson()
    #     await ctx.send("Event messages created")

    @command(aliases=["upde"])
    async def updateevent(self, ctx: Context, event: ArgEvent, import_db: bool = False):
        """Import database, update embed and reactions on a single event message."""  # NOQA
        if await update_event(event, self.bot, import_db=import_db):
            await ctx.send("Event updated")
        else:
            await ctx.send("No changes required")

    @command(aliases=["syncm"])
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
        if isinstance(error, MissingRequiredArgument):
            await ctx.send(f"Missing argument. See: `{CMD}help {ctx.command}`")
            return
        if isinstance(error, BadArgument):
            await ctx.send(f"Invalid argument: {error}. See: `{CMD}help {ctx.command}`")
            return
        if isinstance(error, CommandInvokeError):
            if isinstance(error.original, UnexpectedRole):
                await ctx.send(
                    f"Malformed data: {error.original}. "
                    f"See: `{CMD}help {ctx.command}`"
                )
                return
            if isinstance(error.original, RoleError):
                await ctx.send(
                    f"An error occured: ```{error.original}```\n"
                    f"Message: `{ctx.message.clean_content}`"
                )
                return
            error = error.original

        logging.error(
            "".join(traceback.format_exception(type(error), error, error.__traceback__))
        )
        trace = "".join(
            traceback.format_exception(type(error), error, error.__traceback__, 2)
        )

        if hasattr(ctx, "message"):
            lines = ctx.message.clean_content.split("\n")
            clean_content = ctx.message.clean_content
        else:
            lines = "No associated message"
            clean_content = lines

        logging.error(f"{lines=}")
        if len(lines) > 1:
            # Show only first line of the message
            message = f"{lines[0]} [...]"
        else:
            message = lines[0]
        msg = (
            f"Unexpected error occured: ```{error}```\n"
            f"Message: `{message}`\n\n```py\n{trace}```"
        )
        if len(msg) >= 2000:
            await ctx.send(
                "commandListener: Received error message that's over 2000 "
                "characters, check the log for the full error."
            )
            logging.error("Message:", clean_content)
            msg = f"{msg[:1990]} [...]```"
        await ctx.send(msg)


def setup(bot: OperationBot):
    # importlib.reload(Event)
    importlib.reload(cfg)
    bot.add_cog(CommandListener(bot))
