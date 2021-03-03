from typing import Dict, List, Optional

from discord import ClientUser, Emoji, Message, NotFound, TextChannel
from discord.abc import Messageable
from discord.ext.commands import Context

import config as cfg
from event import Event

# from operationbot import OperationBot


async def getEventMessage(event: Event, bot, archived=False) \
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


async def sortEventMessages(target: Messageable, bot=None):
    """Sort events in event database."""
    if bot is None:
        if isinstance(target, Context):
            bot = target.bot
        else:
            raise ValueError("Requires either the bot argument or context.")

    from eventDatabase import EventDatabase
    EventDatabase.sortEvents()
    print(EventDatabase.events)


    event: Event
    for event in EventDatabase.events.values():
        message = await getEventMessage(event, bot)
        if message is None:
            await target.send(
                "sortEventMessages: No message found with that message ID: {}"
                .format(event.messageID))
            return
        await updateReactions(event, message=message)
        await updateMessageEmbed(message, event)


# from EventDatabase
async def createEventMessage(event: Event, channel: TextChannel,
        update_id=True) -> Message:
    """Create a new event message."""
    # Create embed and message
    embed = event.createEmbed()
    embed.set_footer(text="Event ID: " + str(event.id))
    message = await channel.send(embed=embed)
    if update_id:
        event.messageID = message.id

    return message


# was: EventDatabase.updateEvent
async def updateMessageEmbed(eventMessage: Message, updatedEvent: Event) \
        -> None:
    """Update the embed and footer of a message."""
    newEventEmbed = updatedEvent.createEmbed()
    newEventEmbed.set_footer(text="Event ID: " + str(updatedEvent.id))
    await eventMessage.edit(embed=newEventEmbed)


# from EventDatabase
async def updateReactions(event: Event, message: Message = None, bot=None,
                          reorder=False):
    """
    Update reactions of an event message.

    Requires either the `message` or `bot` argument to be provided. Calling
    the function with reorder = True causes all reactions to be removed and
    reinserted in the correct order.
    """
    if message is None:
        if bot is None:
            raise ValueError("Requires either the `message` or `bot` argument"
                             " to be provided")
        message = await getEventMessage(event, bot)

    reactions: List[Emoji] = event.getReactions()
    reactionsCurrent = message.reactions
    reactionEmojisCurrent = {}
    reactionsToRemove = []
    reactionEmojisToAdd = []

    # Find current reaction emojis
    for reaction in reactionsCurrent:
        reactionEmojisCurrent[reaction.emoji] = reaction

    if list(reactionEmojisCurrent) == reactions:
        # Emojis are already correct, no need for further edits
        return

    if reorder:
        # Re-adding all reactions in order to put them in the correct order
        await message.clear_reactions()
        reactionEmojisToAdd = reactions
    else:
        # Find emojis to remove
        for emoji, reaction in reactionEmojisCurrent.items():
            if emoji not in reactions:
                reactionsToRemove.append(reaction)

        # Find emojis to add
        for emoji in reactions:
            if emoji not in reactionEmojisCurrent.keys():
                reactionEmojisToAdd.append(emoji)

        # Remove existing unintended reactions
        for reaction in reactionsToRemove:
            await message.clear_reaction(reaction)

    # Add missing emojis
    for emoji in reactionEmojisToAdd:
        await message.add_reaction(emoji)


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
        else:
            print("missing a message for event {}, creating".format(event))
            message = await createEventMessage(event, bot.eventchannel)

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
