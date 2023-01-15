import re
from datetime import date, datetime, time
from typing import cast

from discord import Member, Message
from discord.ext.commands.context import Context
from discord.ext.commands.converter import MemberConverter
from discord.ext.commands.errors import (BadArgument, CommandError,
                                         MemberNotFound)

import config as cfg
import messageFunctions as msgFnc
from errors import EventNotFound, MessageNotFound, RoleNotFound
from event import Event
from eventDatabase import EventDatabase
from operationbot import OperationBot
from role import Role

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
        raise ValueError(f"{argument} is not a number or a numeral.") \
            from e
    try:
        return cfg.ADDITIONAL_ROLE_NAMES.index(argument)
    except ValueError as e:
        raise ValueError(f"{argument} is not a number or a numeral.") \
            from e


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

    EMOJI_PATTERN = r'<a?:([a-zA-Z0-9_])+:[0-9]+>'

    @classmethod
    async def convert(cls, ctx: Context, argument: str) -> Role:
        argument = UnquotedStr.unquote(argument)
        try:
            event: Event = ctx.args[2]
            assert isinstance(event, Event)
        except (IndexError, AssertionError) as e:
            raise CommandError(f"The command {ctx.command} is invalid. "
                               "The ArgRole converter requires an Event to be "
                               "the first argument of the calling command") \
                from e
        additional = event.getRoleGroup("Additional")
        first_arg = argument.split(' ')[0]
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
        if (argument.startswith('"') and argument.endswith('"')
                or argument.startswith("'") and argument.endswith("'")):
            return argument[1:-1]
        return argument


class ArgEvent(Event):
    @classmethod
    async def convert(cls, _: Context, arg: str) -> Event:
        return await cls._convert(arg)

    @classmethod
    async def _convert(cls, arg: str, archived=False) -> Event:
        is_integer = True
        try:
            event_id = int(arg)
        except ValueError:
            # Argument is not an integer, so it might be a date
            is_integer = False
        else:
            try:
                return EventDatabase.getEventByID(event_id, archived)
            except EventNotFound:
                # Argument could be a date that looks like an integer (e.g.
                # yymmdd, etc)
                pass

        try:
            event_date = await ArgDate.convert(None, arg)
        except BadArgument as e:
            if is_integer:
                raise BadArgument(
                    f"No event with the given ID {event_id} was found. "
                    f"{str(e)}"
                ) from e
            raise e

        try:
            return EventDatabase.get_event_by_date(event_date)
        except ValueError as e:
            raise BadArgument(str(e)) from e
        except EventNotFound as e:
            raise BadArgument(str(e)) from e


class ArgArchivedEvent(ArgEvent):
    @classmethod
    async def convert(cls, _: Context, arg: str) -> Event:
        return await cls._convert(arg, archived=True)


class ArgDateTime(datetime):
    @classmethod
    async def convert(cls, _: Context, arg: str) -> datetime:
        _date = await ArgDate.convert(None, arg)
        # FIXME: Remove hardcoded time
        return datetime.combine(_date, time(hour=18, minute=30))


class ArgDate(date):
    @classmethod
    async def convert(cls, _: Context, arg: str) -> date:
        try:
            return date.fromisoformat(arg)
        except ValueError:
            pass

        try:
            return cls._convert_date(arg)
        except ValueError as e:
            raise BadArgument(str(e)) from e

    @classmethod
    def _convert_date(cls, arg: str) -> date:
        formats = [
            # yyyy-mm-dd is already handled by date.fromisoformat()
            ('%Y%m%d', 'yyyymmdd'),
            ('%y-%m-%d', 'yy-mm-dd'),
            ('%y%m%d', 'yymmdd'),
            ('%m-%d', 'mm-dd'),
            ('--%m%d', '--mmdd'),
            # 'mmdd' is not allowed because it is too ambiguous (looks like an
            # event ID)
        ]
        for fmt in ([f[0] for f in formats]):
            try:
                event_date = datetime.strptime(arg, fmt).date()
                if event_date.year == 1900:
                    event_date = event_date.replace(year=datetime.now().year)
                return event_date
            except ValueError:
                pass
        raise ValueError(
            f"Invalid date format {arg}. "
            "Has to be one of yyyy-mm-dd, "
            f"{', '.join([f[1] for f in formats])}"
        )


class ArgTime(time):
    @classmethod
    async def convert(cls, _: Context, arg: str) -> time:
        for fmt in ('%H:%M', '%H%M'):
            try:
                _date = datetime.strptime(arg, fmt)
                return time(_date.hour, _date.minute)
            except ValueError:
                pass
        raise BadArgument(f"Invalid time format {arg}. "
                          "Has to be HH:MM or HHMM")


class ArgMessage(Message):
    @classmethod
    async def convert(cls, ctx: Context, arg: str) -> Message:
        try:
            event_id = int(arg)
        except ValueError as e:
            raise BadArgument(f"Invalid message ID {arg}, needs to be an "
                              "integer") from e
        try:
            event = EventDatabase.getEventByID(event_id)
            message = await msgFnc.getEventMessage(
                event, cast(OperationBot, ctx.bot))
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
        name_regex = re.compile(f'^([A-Z]\\. )?{argument}( \\(.+/.+\\))?$'
                                .lower())
        guild = ctx.guild
        if guild is not None:
            for member in guild.members:
                if name_regex.match(member.display_name.lower()):
                    return member
        raise MemberNotFound(f"{argument} is not a valid member")
