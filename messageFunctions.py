from typing import Optional

from discord import Message, NotFound
from discord.ext.commands import Context

import config as cfg
from event import Event
from operationbot import OperationBot


async def getEventMessage(bot: OperationBot, event: Event, archived=False) \
        -> Optional[Message]:
    """Get a message related to an event."""
    if archived:
        channel = bot.eventarchivechannel
    else:
        channel = bot.eventchannel

    try:
        return await channel.fetch_message(event.messageID)
    except NotFound:
        return None


async def getEvent(messageID, ctx: Context) -> Optional[Event]:
    """Get an event by a message id."""
    from eventDatabase import EventDatabase
    eventToUpdate = EventDatabase.getEventByMessage(messageID)
    if eventToUpdate is None:
        await ctx.send("getEvent: No event found with that message ID: {}"
                       .format(messageID))
        return None
    return eventToUpdate


async def sortEventMessages(ctx: Context):
    """Sort events in event database."""
    from eventDatabase import EventDatabase
    EventDatabase.sortEvents()
    print(EventDatabase.events)

    event: Event
    for event in EventDatabase.events.values():
        messageID = event.messageID
        eventchannel = ctx.bot.get_channel(cfg.EVENT_CHANNEL)
        try:
            eventMessage = await eventchannel.fetch_message(messageID)
        except NotFound:
            await ctx.send(
                "sortEventMessages: No message found with that message ID: {}"
                .format(messageID))
            return
        reactions = event.getReactions()
        await EventDatabase.updateReactions(eventMessage, reactions,
                                            ctx.bot.user)
        await EventDatabase.updateEvent(eventMessage, event)
