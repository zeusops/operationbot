from typing import Optional

from discord import Message, NotFound
from discord.ext.commands import Bot, Context

import config as cfg
from event import Event


async def getEventMessage(bot: Bot, event: Event) -> Optional[Message]:
    # Get channels
    eventchannel = bot.get_channel(cfg.EVENT_CHANNEL)

    # Get message
    try:
        return await eventchannel.fetch_message(event.messageID)
    except NotFound:
        return None

async def getEvent(messageID, ctx: Context) -> Optional[Event]:
    from eventDatabase import EventDatabase
    eventToUpdate = EventDatabase.getEventByMessage(messageID)
    if eventToUpdate is None:
        await ctx.send("No event found with that message ID")
        return None
    return eventToUpdate


async def sortEventMessages(ctx: Context):
    """Sort events in event database"""
    from eventDatabase import EventDatabase
    EventDatabase.sortEvents()
    print(EventDatabase.events)

    for event in EventDatabase.events.values():
        messageID = event.messageID
        eventchannel = ctx.bot.get_channel(cfg.EVENT_CHANNEL)
        try:
            eventMessage = await eventchannel.fetch_message(messageID)
        except NotFound:
            await ctx.send("No message found with that message ID")
            return
        await EventDatabase.updateReactions(eventMessage, event, ctx.bot)
        await EventDatabase.updateEvent(eventMessage, event)

