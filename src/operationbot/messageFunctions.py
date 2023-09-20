import logging
from typing import Dict, List, Union, cast

from discord import Emoji, Message, NotFound, TextChannel
from discord.embeds import Embed
from discord.errors import Forbidden, HTTPException

from operationbot.bot import OperationBot
from operationbot.errors import EventUpdateFailed, MessageNotFound, RoleError
from operationbot.event import Event
from operationbot.eventDatabase import EventDatabase


async def getEventMessage(event: Event, bot: OperationBot, archived=False) -> Message:
    """Get a message related to an event."""
    if archived:
        channel = bot.eventarchivechannel
    else:
        channel = bot.eventchannel

    try:
        return await channel.fetch_message(event.messageID)
    except NotFound as e:
        raise MessageNotFound(
            f"No event message found with message ID {event.messageID}"
        ) from e


async def sortEventMessages(bot: OperationBot):
    """Sort event messages according to the event database.

    Saves the database to disk after sorting.

    Raises MessageNotFound if messages are missing.
    """
    logging.info("sortEventMessages")
    EventDatabase.sortEvents()

    event: Event
    for event in EventDatabase.events.values():
        try:
            message = await getEventMessage(event, bot)
        except MessageNotFound as e:
            raise MessageNotFound(f"sortEventMessages: {e}") from e
        await updateMessageEmbed(message, event)
        await updateReactions(event, message=message)
    EventDatabase.toJson()


# from EventDatabase
async def createEventMessage(
    event: Event, channel: TextChannel, update_id=True
) -> Message:
    """Create a new event message."""
    # Create embed and message
    embed = event.createEmbed(cache=False)
    message = await channel.send(embed=embed)
    if update_id:
        event.messageID = message.id

    return message


# was: EventDatabase.updateEvent
async def updateMessageEmbed(eventMessage: Message, updatedEvent: Event) -> bool:
    """Update the embed and footer of a message."""
    embed = updatedEvent.createEmbed()
    if embed:
        try:
            await eventMessage.edit(embed=embed)
        except HTTPException as e:
            # Failed to edit the newly-created embed in (probably due to a rate
            # limit), invalidating the embed hash and saving the database
            # before propagating the exception
            updatedEvent.embed_hash = ""
            EventDatabase.toJson()
            raise EventUpdateFailed(
                f"Failed to update embed for {updatedEvent} "
                f"on message {eventMessage}"
            ) from e
        return True
    return False


# from EventDatabase
async def updateReactions(
    event: Event, message: Message | None = None, bot=None, reorder=False
):
    """Update reactions of an event message.

    Requires either the `message` or `bot` argument to be provided. Calling
    the function with reorder = True causes all reactions to be removed and
    reinserted in the correct order.
    """
    if message is None:
        if bot is None:
            raise ValueError(
                "Requires either the `message` or `bot` argument to be provided"
            )
        message = await getEventMessage(event, bot)

    reactions: List[Union[Emoji, str]] = event.getReactions()
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
            if emoji not in reactionEmojisCurrent:
                reactionEmojisToAdd.append(emoji)

        # Remove existing unintended reactions
        for reaction in reactionsToRemove:
            await message.clear_reaction(reaction)

    # Add missing emojis
    for emoji in reactionEmojisToAdd:
        try:
            await message.add_reaction(emoji)
        except Forbidden as e:
            if e.code == 30010:
                raise RoleError(
                    "Too many reactions, not adding role "
                    f"{emoji}. This should not happen."
                ) from e


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
    if len(message.embeds) == 0:
        raise ValueError("Message has no embeds")
    footer = message.embeds[0].footer
    if footer.text == Embed.Empty:
        raise ValueError("Footer is empty")
    # Casting because mypy doesn't detect correctly that the type of
    # footer.text has been checked already
    return int(cast(str, footer.text).split(" ")[-1])


async def syncMessages(events: Dict[int, Event], bot: OperationBot):
    """Sync event messages with the event database.

    Saves the database to disk after syncing.
    """
    logging.info("syncMessages")
    sorted_events = sorted(
        list(events.values()), key=lambda event: event.date, reverse=True
    )
    for event in sorted_events:
        try:
            message = await getEventMessage(event, bot)
        except MessageNotFound:
            print(f"Missing a message for event {event}, creating")
            await createEventMessage(event, bot.eventchannel)
        else:
            if messageEventId(message) == event.id:
                print(f"Found message {message.id} for event {event}")
            else:
                print(
                    f"Found incorrect message for event {event}, deleting "
                    f"and creating"
                )
                # Technically multiple events might have the same saved
                # messageID but it's simpler to just recreate messages here if
                # the event ID doesn't match
                await message.delete()
                await createEventMessage(event, bot.eventchannel)

    await sortEventMessages(bot)


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
