from typing import Dict, List, Union, cast

from discord import Message, NotFound, TextChannel
from discord.embeds import Embed
from discord.emoji import Emoji
from discord.errors import Forbidden
from discord.partial_emoji import PartialEmoji
from discord.reaction import Reaction

from errors import ExtraMessagesFound, MessageNotFound, RoleError
from event import Event
from eventDatabase import EventDatabase
from operationbot import OperationBot
from role import ReactionEmoji


async def getEventMessage(event: Event, bot: OperationBot = None,
                          archived=False, message_id=None,
                          channel: TextChannel = None) \
        -> Message:
    """Get the a single message related to an event.

    if message_id is not set, returns the first (main) message"""
    if channel is None:
        if bot is None:
            raise ValueError("Requires either the `channel` or `bot` "
                             "argument to be provided")
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


async def getEventMessages(event: Event, bot: OperationBot = None,
                           archived=False, channel: TextChannel = None,
                           exact_number=True) \
        -> List[Message]:
    """Get all messages related to an event.

    Raises MessageNotFound if the message is missing or if the event embeds
    require more messages than can currently be found.

    If exact_number is set, also raises an error if too many messages can be
    found."""
    messages = []
    for messageID in event.messageIDList:
        messages.append(await getEventMessage(
            event, bot=bot, archived=archived, message_id=messageID,
            channel=channel))
    embeds, _ = event.createEmbeds()
    if len(messages) < len(embeds):
        raise MessageNotFound("Not all event messages found")
    if exact_number and len(messages) > len(embeds):
        raise ExtraMessagesFound("Too many event messages found")
    return messages


async def sortEventMessages(bot: OperationBot):
    """Sort events in event database.

    Raises MessageNotFound if messages are missing."""
    EventDatabase.sortEvents()

    for event in EventDatabase.events.values():
        messageList = await get_or_create_messages(event, bot.eventchannel)
        await updateMessageEmbeds(messageList, event, bot.eventchannel)
    for event in EventDatabase.events.values():
        # Updating reactions takes a while, so we do it in a separate task
        await updateReactions(event, bot=bot)


async def get_or_create_messages(event: Event, channel: TextChannel,
                                 update_id=True) -> List[Message]:
    """Create new or missing event messages, delete extra messages."""
    try:
        all_messages = await getEventMessages(event, channel=channel)
    except (MessageNotFound, ExtraMessagesFound):
        pass
    else:
        # All messages were found without issues, nothing to do
        return all_messages

    messages: List[Message] = []
    not_found: List[int] = []
    for message_id in event.messageIDList:
        try:
            message = await getEventMessage(event, message_id=message_id,
                                            channel=channel)
            messages.append(message)
        except MessageNotFound:
            not_found.append(message_id)

    # Get all message IDs that corresponded to an existing message
    message_ids = [x for x in event.messageIDList if x not in not_found]

    embeds, _ = event.createEmbeds()
    existing_messages = len(message_ids)
    difference = existing_messages - len(embeds)
    if difference > 0:
        # We have extra messages that need to be deleted. We could try to reuse
        # the messages for other events instead of deleting, but keeping track
        # of that would be too complicated.
        for message_id in message_ids[difference:]:
            message = await channel.fetch_message(message_id)
            if message in messages:
                messages.remove(message)
            await message.delete()
    elif difference < 0:
        # We have too few messages, create new ones
        for i in range(abs(difference)):
            # The embeds will be correct if there were no existing messages
            # to begin with (when running the `show` command). Otherwise the
            # will be updated afterwards anyway.
            message = await channel.send(embed=embeds[existing_messages + i])
            messages.append(message)

    if update_id:
        message_ids = [message.id for message in messages]
        event.messageIDList = list(message_ids)

    return messages


async def updateMessageEmbeds(eventMessageList: List[Message],
                              event: Event, channel: TextChannel) \
        -> None:
    """Update the embed and footer of a message."""
    embeds, _ = event.createEmbeds()
    if len(embeds) == len(eventMessageList):
        for message, embed in zip(eventMessageList, embeds):
            await message.edit(embed=embed)
    else:
        messages = await get_or_create_messages(event, channel)
        await updateMessageEmbeds(messages, event, channel)


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

    # TODO: reactions is a list of lists: outer list per embed, inner list
    # reactions of that embed. Should loop over messages and lists of reactions
    _, all_reactions = event.createEmbeds()
    for message, reactions in zip(messageList, all_reactions):
        current_reactions: Dict[Union[Emoji, PartialEmoji, str], Reaction] = {}
        new_reactions: List[ReactionEmoji] = []
        # Find current reaction emojis
        for reaction in message.reactions:
            current_reactions[reaction.emoji] = reaction

        if list(current_reactions) == reactions:
            # Emojis are already correct, moving to next message
            continue

        if reorder:
            # Re-adding all reactions in order to put them in the correct order
            await message.clear_reactions()
            new_reactions = reactions
        else:
            # Find emojis to remove
            for emoji, reaction in current_reactions.items():
                if emoji not in reactions:
                    await message.clear_reaction(reaction)

            # Find emojis to add
            for new_reaction in reactions:
                if new_reaction not in current_reactions.keys():
                    new_reactions.append(new_reaction)

        # Add missing emojis
        for new_reaction in new_reactions:
            try:
                await message.add_reaction(new_reaction)
            except Forbidden as e:
                if e.code == 30010:
                    raise RoleError(
                        f"Too many reactions, not adding role {new_reaction}. "
                        "This should not happen.") from e


def _messageEventId(message: Message) -> int:
    if len(message.embeds) == 0:
        raise ValueError("Message has no embeds")
    footer = message.embeds[0].footer
    if footer.text == Embed.Empty:
        raise ValueError("Footer is empty")
    # Casting because mypy doesn't detect correctly that the type of
    # footer.text has been checked already
    return int(cast(str, footer.text).split(' ')[-1])


async def syncMessages(events: Dict[int, Event], bot: OperationBot):
    sorted_events = sorted(list(events.values()), key=lambda event: event.date)
    for event in sorted_events:
        missing_ids = []
        new_ids = []
        for message_id in event.messageIDList:
            try:
                message = await getEventMessage(event, bot,
                                                message_id=message_id)
            except MessageNotFound:
                print(f"Missing a message for event {event}, creating")
                message = await bot.eventchannel.send(
                    embed=event.create_dummy_embed())
                new_ids.append(message.id)
                missing_ids.append(message_id)
            else:
                if _messageEventId(message) == event.id:
                    print(f"Found message {message.id} for event {event}")
                else:
                    print(f"Found incorrect message for event {event}, "
                          f"deleting and creating")
                    # Technically multiple events might have the same saved
                    # messageID but it's simpler to just recreate messages here
                    # if the event ID doesn't match
                    await message.delete()
                    await _send_message(event, bot.eventchannel)
                    missing_ids.append(message_id)
        # Remove missing or deleted IDs
        event.messageIDList = [x for x in event.messageIDList
                               if x not in missing_ids] + new_ids

    await sortEventMessages(bot)


async def _send_message(event: Event, channel: TextChannel):
    message = await channel.send(embed=event.create_dummy_embed())
    event.messageIDList.append(message.id)
