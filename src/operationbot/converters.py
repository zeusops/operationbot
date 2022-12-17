import re
from datetime import date, datetime, time
from typing import cast

from discord import Member, Message
from discord.ext.commands.context import Context
from discord.ext.commands.converter import MemberConverter
from discord.ext.commands.errors import (
    BadArgument,
    CommandError,
    MemberNotFound,
)

from operationbot import config as cfg
from operationbot import messageFunctions as msgFnc
from operationbot.bot import OperationBot
from operationbot.errors import EventNotFound, MessageNotFound, RoleNotFound
from operationbot.event import Event
from operationbot.eventDatabase import EventDatabase
from operationbot.role import Role

NUMBERS = {
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "ten",
}


def _get_index(argument: str) -> int:
    if argument in cfg.ADDITIONAL_ROLE_EMOJIS:
        return cfg.ADDITIONAL_ROLE_EMOJIS.index(argument)

    try:
        argument = NUMBERS[int(argument)]
    except ValueError:
        # Argument might already be a numeral
        pass
    except KeyError as e:
        raise ValueError(f"{argument} is not a number or a numeral.") from e
    try:
        return cfg.ADDITIONAL_ROLE_NAMES.index(argument)
    except ValueError as e:
        raise ValueError(f"{argument} is not a number or a numeral.") from e


class ArgRole(Role):
    """Converts argument into a Role

    NOTE: A command that uses this converter **must have** the event as the
    first argument to the command.

    Converts the following types of arguments in the following order:
        - Additional role emoji (e.g. :one:)
        - Additional role numeral (e.g. one)
        - Additional role number (e.g. 1)
        - Any role emoji (e.g. :ZEUS:)
        - Any role name (e.g. Zeus)

    Finally, raises a BadArgument if no role was found.
    """

    # NOTE: the third chapter of the docstring (Converts the following [..]) is
    # dynamically parsed and displayed as a part of the `roleparserinfo`
    # command. If the structure of the docstring is changed, the command must
    # be ajusted accordingly.

    EMOJI_PATTERN = r"<a?:([a-zA-Z0-9_])+:[0-9]+>"

    @classmethod
    async def convert(cls, ctx: Context, argument: str) -> Role:
        argument = UnquotedStr.unquote(argument)
        try:
            event: Event = ctx.args[2]
            if not isinstance(event, Event):
                raise ValueError
        except (IndexError, AssertionError) as e:
            raise CommandError(
                f"The command {ctx.command} is invalid. "
                "The ArgRole converter requires an Event to be "
                "the first argument of the calling command"
            ) from e
        additional = event.getRoleGroup("Additional")
        first_arg = argument.split(" ")[0]
        try:
            index = _get_index(first_arg)
        except ValueError:
            # Argument is not a number or a numeral, so it must be either an
            # emoji, an emoji name, or a role name
            pass
        else:
            try:
                return additional.roles[index]
            except IndexError as e:
                raise BadArgument(f"{first_arg} is not a valid role") from e

        match = re.search(cls.EMOJI_PATTERN, first_arg)
        if match:
            # Argument is an emoji
            first_arg = match.group(1)
        try:
            return event.findRoleWithName(first_arg)
        except RoleNotFound:
            # Could not find a role with the first argument, trying with the
            # whole line
            try:
                return event.findRoleWithName(argument)
            except RoleNotFound as e:
                raise BadArgument(f"{argument} is not a valid role") from e


class UnquotedStr(str):
    @classmethod
    async def convert(cls, _: Context, argument: str) -> str:
        return cls.unquote(argument)

    @classmethod
    def unquote(cls, argument: str) -> str:
        if (
            argument.startswith('"')
            and argument.endswith('"')
            or argument.startswith("'")
            and argument.endswith("'")
        ):
            return argument[1:-1]
        return argument


class ArgEvent(Event):
    @classmethod
    async def convert(cls, _: Context, arg: str) -> Event:
        return await cls._convert(arg)

    @classmethod
    async def _convert(cls, arg: str, archived=False) -> Event:
        try:
            event_id = int(arg)
        except ValueError as e:
            raise BadArgument(
                f"Invalid message ID {arg}, needs to be an integer"
            ) from e

        try:
            if not archived:
                event = EventDatabase.getEventByID(event_id)
            else:
                event = EventDatabase.getArchivedEventByID(event_id)
        except EventNotFound as e:
            raise BadArgument(str(e)) from e

        return event


class ArgArchivedEvent(ArgEvent):
    @classmethod
    async def convert(cls, _: Context, arg: str) -> Event:
        return await cls._convert(arg, archived=True)


class ArgDateTime(datetime):
    @classmethod
    async def convert(cls, ctx: Context, arg: str) -> datetime:
        _date = await ArgDate.convert(ctx, arg)
        return datetime.combine(_date, time(hour=18, minute=30))


class ArgDate(date):
    @classmethod
    async def convert(cls, _: Context, arg: str) -> date:
        try:
            return date.fromisoformat(arg)
        except ValueError as e:
            raise BadArgument(
                f"Invalid date format {arg}. Has to be YYYY-MM-DD"
            ) from e


class ArgTime(time):
    @classmethod
    async def convert(cls, _: Context, arg: str) -> time:
        for fmt in ("%H:%M", "%H%M"):
            try:
                _date = datetime.strptime(arg, fmt)
                return time(_date.hour, _date.minute)
            except ValueError:
                pass
        raise BadArgument(
            f"Invalid time format {arg}. Has to be HH:MM or HHMM"
        )


class ArgMessage(Message):
    @classmethod
    async def convert(cls, ctx: Context, arg: str) -> Message:
        try:
            event_id = int(arg)
        except ValueError as e:
            raise BadArgument(
                f"Invalid message ID {arg}, needs to be an integer"
            ) from e
        try:
            event = EventDatabase.getEventByID(event_id)
            message = await msgFnc.getEventMessage(
                event, cast(OperationBot, ctx.bot)
            )
        except (EventNotFound, MessageNotFound) as e:
            raise BadArgument(str(e)) from e

        return message


class ArgMember(Member):
    @classmethod
    async def convert(cls, ctx: Context, argument: str) -> Member:
        try:
            # First try the regular converter
            converter = MemberConverter()
            return await converter.convert(ctx, argument)
        except MemberNotFound:
            pass
        name_regex = re.compile(
            f"^([A-Z]\\. )?{argument}( \\(.+/.+\\))?$".lower()
        )
        guild = ctx.guild
        if guild is not None:
            for member in guild.members:
                if name_regex.match(member.display_name.lower()):
                    return member
        raise MemberNotFound(f"{argument} is not a valid member")
