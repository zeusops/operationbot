from typing import Dict, List, Union, cast

from discord import Emoji, Message, NotFound, TextChannel
from discord.embeds import Embed

from errors import MessageNotFound
from event import Event
from eventDatabase import EventDatabase
from operationbot import OperationBot


async def getEventMessage(event: Event, bot: OperationBot, archived=False,
                          message_id=None) \
        -> Message:
    """Get the a single message related to an event.

    if message_id is not set, returns the first (main) message"""
    if archived:
        channel = bot.eventarchivechannel
    else:
        channel = bot.eventchannel
    if message_id is None:
        message_id = event.messageIDList[0]
    try:
        return await channel.fetch_message(message_id)
    except NotFound as e:
        raise MessageNotFound("No event message found with "
                              f"message ID {message_id}") from e


async def getEventMessages(event: Event, bot: OperationBot, archived=False) \
        -> List[Message]:
    """Get all messages related to an event."""
    messages = []
    for messageID in event.messageIDList:
        messages.append(await getEventMessage(
            event, bot, archived=archived, message_id=messageID))
    return messages


async def sortEventMessages(bot: OperationBot):
    """Sort events in event database.

    Raises MessageNotFound if messages are missing."""
    EventDatabase.sortEvents()

    event: Event
    for event in EventDatabase.events.values():
        try:
            messageList = await getEventMessages(event, bot)
        except MessageNotFound as e:
            raise MessageNotFound(f"sortEventMessages: {e}") from e
        await updateMessageEmbeds(messageList, event, bot.eventchannel)
        await updateReactions(event, messageList=messageList)


async def createEventMessages(event: Event, channel: TextChannel,
                              update_id=True) -> List[Message]:
    """Create new event messages."""
    embeds = event.createEmbeds()
    messages = []
    message_ids = []
    for embed in embeds:
        message = await channel.send(embed=embed)
        messages.append(message)
        message_ids.append(message.id)
    if update_id:
        event.messageIDList = list(message_ids)

    return messages


async def updateMessageEmbeds(eventMessageList: List[Message],
                              event: Event, channel: TextChannel) \
        -> None:
    """Update the embed and footer of a message."""
    embeds = event.createEmbeds()
    if len(embeds) == len(eventMessageList):
        for message, embed in zip(eventMessageList, embeds):
            await message.edit(embed=embed)
    else:
        for message in eventMessageList:
            await message.delete()
        await createEventMessages(event, channel)


async def updateReactions(event: Event, messageList: List[Message] = None,
                          bot: OperationBot = None, reorder=False):
    """
    Update reactions of an event message.

    Requires either the `message` or `bot` argument to be provided. Calling
    the function with reorder = True causes all reactions to be removed and
    reinserted in the correct order.
    """
    # TODO make efficient again (if necessary, works quiet well rn)
    # TODO: Only add missing reactions / remove old ones instead of removing
    #       everything
    if not messageList:
        if bot is None:
            raise ValueError("Requires either the `messageList` or `bot` "
                             "argument to be provided")
        messageList = await getEventMessages(event, bot)

    reactions: List[Union[Emoji, str]] = event.getReactions()
    reactionsCurrent = []
    reactionEmojisCurrent = {}
    for message in messageList:
        reactionsCurrent.extend(message.reactions)

    # Find current reaction emojis
    for reaction in reactionsCurrent:
        reactionEmojisCurrent[reaction.emoji] = reaction

    if list(reactionEmojisCurrent) == reactions:
        # Emojis are already correct, no need for further edits
        return

    for message in messageList:
        await message.clear_reactions()

    if len(reactions) <= event.getReactionsPerMessage():
        # Add Emojis for the first embed with additional Roles
        for emoji in reactions:
            await messageList[0].add_reaction(emoji)
    else:
        # Add Emojis for the first embed without additional Roles
        for i in range((len(reactions) - event.additional_role_count)):
            emoji = reactions.pop(0)
            await messageList[0].add_reaction(emoji)

        # Add Emojis to following embeds
        counter = 0
        messageNumber = 1
        for i in range(len(reactions)):
            emoji = reactions.pop(0)
            await messageList[messageNumber].add_reaction(emoji)

            counter += 1
            if counter == event.getReactionsPerMessage():
                messageNumber += 1
                counter = 0


def messageEventId(message: Message) -> int:
    if len(message.embeds) == 0:
        raise ValueError("Message has no embeds")
    footer = message.embeds[0].footer
    if footer.text == Embed.Empty:
        raise ValueError("Footer is empty")
    # Casting because mypy doesn't detect correctly that the type of
    # footer.text has been checked already
    return int(cast(str, footer.text).split(' ')[-1])


async def syncMessages(events: Dict[int, Event], bot: OperationBot):
    # TODO: Handle multiple message IDs
    sorted_events = sorted(list(events.values()), key=lambda event: event.date)
    for event in sorted_events:
        try:
            message = await getEventMessage(event, bot)
        except MessageNotFound:
            print(f"Missing a message for event {event}, creating")
            await createEventMessages(event, bot.eventchannel)
        else:
            if messageEventId(message) == event.id:
                print(f"Found message {message.id} for event {event}")
            else:
                print(f"Found incorrect message for event {event}, deleting "
                      f"and creating")
                # Technically multiple events might have the same saved
                # messageID but it's simpler to just recreate messages here if
                # the event ID doesn't match
                messageList = await getEventMessages(event, bot)
                for message in messageList:
                    await message.delete()
                await createEventMessages(event, bot.eventchannel)

    await sortEventMessages(bot)
