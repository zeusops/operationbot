from typing import Dict, List, Optional

from discord import ClientUser, Emoji, Message, NotFound, TextChannel
from discord.abc import Messageable
from discord.ext.commands import Context

import config as cfg
from event import Event
from container import Container

# from operationbot import OperationBot

async def getEventMessage(event: Event, bot) \
        -> Optional[Message]:
    """Get a message related to an event."""
    if event.container is not None:
        return event.container.getMessage(bot)
    else:
        if event.archived:
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

async def sortEventMessages(target: Messageable, bot=None):
    """Sort events in event database."""
    if bot is None:
        if isinstance(target, Context):
            bot = target.bot
        else:
            raise ValueError("Requires either the bot argument or context.")

    Container.sortEvents()
    from eventDatabase import EventDatabase
    print(EventDatabase.events)


    for container in [event.container for event in EventDatabase.events.values()]:
        message = await container.getMessage(bot)
        if message is None:
            await target.send(
                "sortEventMessages: No message found with that message ID: {}"
                .format(container.id))
            return
        await container.updateReactions(message=message)
        await container.updateEmbed()

# async def createMessages(events: Dict[int, Event], bot):
#     # Update event message contents and add reactions

#     # Clear events channel
#     if cfg.PURGE_ON_CONNECT:
#         await bot.eventchannel.purge(limit=100)

#     for event in events.values():
#         await createEventMessage(event, bot.eventchannel)
#     for event in events.values():
#         message = await getEventMessage(event, bot)
#         await updateMessageEmbed(message, event)
#         await updateReactions(event, bot=bot)

def messageEventId(message: Message) -> int:
    footer = message.embeds[0].footer.text
    return int(footer.split(' ')[-1])

async def syncMessages(events: Dict[int, Event], bot):
    sorted_events = sorted(list(events.values()), key=lambda event: event.date)
    print(sorted_events)
    for event in sorted_events:
        message = await getEventMessage(event, bot)
        if message is not None and messageEventId(message) == event.id:
            print("found message {} for event {}".format(message.id, event))
            if event.container is None:
                print("event {} does not have a container, creating"
                      .format(event))
                event.container = Container(event, bot.eventchannel, message)
        else:
            print("missing a message for event {}, creating".format(event))
            message = await Container.send(event, bot.eventchannel)

    await sortEventMessages(bot.commandchannel, bot)

# async def importMessages(events: Dict[int, Event], bot):
#     found = 0
#     async for message in bot.eventchannel.history():
#         if len(message.embeds) > 0:
#             print("embeds", message.embeds)
#             footer = message.embeds[0].footer.text
#             print("footer", footer)
#             event_id = int(footer.split(' ')[-1])
#             if event_id in events:
#                 events[event_id].messageID = message.id
#                 found += 1
#             else:
#                 print("Found a message {} with unknown event id {}"
#                       .format(message.id, event_id))
#             if found >= len(events):
#                 print("Found all messages")
#                 break
