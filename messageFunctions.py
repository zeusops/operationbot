from typing import Dict, List, Union, cast

from discord import Emoji, Message, NotFound, TextChannel
from discord.embeds import Embed

from errors import MessageNotFound
from event import Event
from eventDatabase import EventDatabase
from operationbot import OperationBot


async def getEventMessage(event: Event, bot: OperationBot, archived=False) \
        -> List[Message]:
    """Get a message related to an event."""
    if archived:
        channel = bot.eventarchivechannel
    else:
        channel = bot.eventchannel

    try:
        messageIDList = []
        for messageID in event.messageIDList:
            messageIDList.append(await channel.fetch_message(messageID))
        return messageIDList
    except NotFound as e:
        raise MessageNotFound("No event message found with "
                              f"message ID {event.messageIDList}") from e


async def sortEventMessages(bot: OperationBot):
    """Sort events in event database.

    Raises MessageNotFound if messages are missing."""
    EventDatabase.sortEvents()

    event: Event
    for event in EventDatabase.events.values():
        try:
            messageList = await getEventMessage(event, bot)
        except MessageNotFound as e:
            raise MessageNotFound(f"sortEventMessages: {e}") from e
        await updateMessageEmbed(messageList, event, bot.eventchannel)
        await updateReactions(event, messageList=messageList)


# from EventDatabase
async def createEventMessage(event: Event, channel: TextChannel,
                             update_id=True) -> Message:
    """Create a new event message."""
    # Create embeds and messages
    embeds = event.createEmbeds()
    if update_id:
        event.messageIDList.clear()
        for embed in embeds:
            message = await channel.send(embed=embed)
            event.messageIDList.append(message.id)
    else:
        for embed in embeds:
            message = await channel.send(embed=embed)

    return message


# was: EventDatabase.updateEvent
async def updateMessageEmbed(eventMessageList: List[Message],
                             updatedEvent: Event, channel: TextChannel) \
        -> None:
    """Update the embed and footer of a message."""
    newEventEmbedList = updatedEvent.createEmbeds()
    if len(newEventEmbedList) == len(eventMessageList):
        for i in range(len(newEventEmbedList)):
            await eventMessageList[i].edit(embed=newEventEmbedList[i])
    else:
        for eventMessage in eventMessageList:
            await eventMessage.delete()
        await createEventMessage(updatedEvent, channel)


# from EventDatabase
async def updateReactions(event: Event, messageList: List[Message] = None,
                          bot=None, reorder=False):
    """
    Update reactions of an event message.

    Requires either the `message` or `bot` argument to be provided. Calling
    the function with reorder = True causes all reactions to be removed and
    reinserted in the correct order.
    """
    # TODO make efficient again (if necessary, works quiet well rn)
    if not messageList:
        if bot is None:
            raise ValueError("Requires either the `messageList` or `bot` "
                             "argument to be provided")
        messageList = await getEventMessage(event, bot)

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
            messageList = await getEventMessage(event, bot)
        except MessageNotFound:
            print(f"Missing a message for event {event}, creating")
            await createEventMessage(event, bot.eventchannel)
        else:
            if messageEventId(messageList[0]) == event.id:
                print(f"Found message {messageList[0].id} for event {event}")
            else:
                print(f"Found incorrect message for event {event}, deleting "
                      f"and creating")
                # Technically multiple events might have the same saved
                # messageID but it's simpler to just recreate messages here if
                # the event ID doesn't match
                for message in messageList:
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
