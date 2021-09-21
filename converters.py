from datetime import date, datetime, time
from typing import cast

from discord import Message
from discord.ext.commands.context import Context
from discord.ext.commands.errors import BadArgument

import messageFunctions as msgFnc
from errors import EventNotFound, MessageNotFound
from event import Event
from eventDatabase import EventDatabase
from operationbot import OperationBot


class ArgEvent(Event):
    @classmethod
    async def convert(cls, _: Context, arg: str) -> Event:
        return await cls._convert(arg)

    @classmethod
    async def _convert(cls, arg: str, archived=False) -> Event:
        try:
            event_id = int(arg)
        except ValueError as e:
            raise BadArgument(f"Invalid message ID {arg}, needs to be an "
                              "integer") from e

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
            raise BadArgument(f"Invalid date format {arg}. "
                              "Has to be YYYY-MM-DD") from e


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
