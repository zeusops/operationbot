import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from discord import ClientUser, Emoji, Message, TextChannel

import config as cfg
from event import Event
from messageFunctions import getEventMessage
from operationbot import OperationBot

DATABASE_VERSION = 3


class EventDatabase:
    """Represents a database containing current events."""

    events: Dict[int, Event] = {}
    eventsArchive: Dict[int, Event] = {}
    nextID: int = 0

    @staticmethod
    async def createEvent(date: datetime, channel: TextChannel,
                          importing=False, eventID=-1) \
            -> Tuple[Message, Event]:
        """Create a new event and store it."""
        if eventID == -1:
            eventID = EventDatabase.nextID

        # Create event
        event = Event(date, channel.guild.emojis, eventID=eventID,
                      importing=importing)

        # Create message
        message = await EventDatabase.createEventMessage(event, channel)
        event.messageID = message.id

        # Store event
        EventDatabase.events[event.id] = event

        if not importing:
            EventDatabase.nextID += 1

        return message, event

    # Create a new event message
    @staticmethod
    async def createEventMessage(event: Event, channel: TextChannel) \
            -> Message:
        # Create embed and message
        embed = event.createEmbed()
        embed.set_footer(text="Event ID: " + str(event.id))
        message = await channel.send(embed=embed)

        return message

    @staticmethod
    def archiveEvent(event: Event):
        """
        Move event to archive.

        Does not remove or create messages.
        """
        # Remove event from events
        EventDatabase.removeEvent(event.id)

        # Add event to eventsArchive
        EventDatabase.eventsArchive[event.id] = event

    @staticmethod
    async def updateEvent(eventMessage: Message, updatedEvent: Event) -> None:
        """Update an existing event and store it."""
        newEventEmbed = updatedEvent.createEmbed()
        newEventEmbed.set_footer(text="Event ID: " + str(updatedEvent.id))
        updatedEvent.messageID = eventMessage.id
        await eventMessage.edit(embed=newEventEmbed)

        # Store event
        EventDatabase.events[updatedEvent.id] = updatedEvent

    @staticmethod
    def removeEvent(eventID: int, archived=False) -> bool:
        """
        Remove event.

        Does not remove the message associated with the event.
        """
        if archived:
            if eventID in EventDatabase.eventsArchive.keys():
                del EventDatabase.eventsArchive[eventID]
                return True
        else:
            if eventID in EventDatabase.events.keys():
                del EventDatabase.events[eventID]
                return True
        return False

    # was: findEvent
    @staticmethod
    def getEventByMessage(messageID: int) -> Optional[Event]:
        """Find an event with it's message ID."""
        event: Event
        for event in EventDatabase.events.values():
            if event.messageID == messageID:
                return event
        return None

    @staticmethod
    def getEventByID(eventID: int) -> Optional[Event]:
        """Find an event with it's ID."""
        return EventDatabase.events.get(eventID)

    @staticmethod
    def getArchivedEventByMessage(messageID: int) -> Optional[Event]:
        # return EventDatabase.eventsArchive.get(messageID)
        for event in EventDatabase.eventsArchive.values():
            if event.messageID == messageID:
                return event
        return None

    # was: findEventInArchiveeventid
    @staticmethod
    def getArchivedEventByID(eventID: int):
        return EventDatabase.eventsArchive.get(eventID)

    @staticmethod
    def sortEvents():
        sortedEvents = []
        messageIDs = []

        # Store existing events
        for event in EventDatabase.events.values():
            sortedEvents.append(event)
            messageIDs.append(event.messageID)

        # Sort events based on date and time
        sortedEvents.sort(key=lambda event: event.date, reverse=True)
        messageIDs.sort(reverse=True)

        # Fill events again
        EventDatabase.events: Dict[int, Event] = {}
        for event in sortedEvents:
            # event = sortedEvents[index]
            event.messageID = messageIDs.pop()
            EventDatabase.events[event.id] = event

    @staticmethod
    async def updateReactions(message: Message, reactions: List[Emoji],
                              user: ClientUser):
        reactionEmojisIntended = reactions
        reactionsCurrent = message.reactions
        reactionEmojisCurrent = {}
        reactionsToRemove = []
        reactionEmojisToAdd = []

        # Find reaction emojis current
        for reaction in reactionsCurrent:
            reactionEmojisCurrent[reaction.emoji] = reaction

        # Find emojis to remove
        for emoji, reaction in reactionEmojisCurrent.items():
            if emoji not in reactionEmojisIntended:
                reactionsToRemove.append(reaction)

        # Find emojis to add
        for emoji in reactionEmojisIntended:
            if emoji not in reactionEmojisCurrent.keys():
                reactionEmojisToAdd.append(emoji)

        # Remove existing unintended reactions
        for reaction in reactionsToRemove:
            await message.remove_reaction(reaction, user)

        # Add not existing intended emojis
        for emoji in reactionEmojisToAdd:
            await message.add_reaction(emoji)

    @staticmethod
    def toJson():
        # Get eventsData
        eventsData = {}
        for messageID, event in EventDatabase.events.items():
            eventsData[messageID] = event.toJson()

        # Get eventsArchiveData
        eventsArchiveData = {}
        for messageID, event in EventDatabase.eventsArchive.items():
            eventsArchiveData[messageID] = event.toJson()

        # Store data and return
        data = {}
        data['version'] = DATABASE_VERSION
        data['nextID'] = EventDatabase.nextID
        data['events'] = eventsData
        data['eventsArchive'] = eventsArchiveData

        with open(cfg.JSON_FILEPATH, 'w') as jsonFile:
            json.dump(data, jsonFile, indent=2)

    @staticmethod
    async def fromJson(bot: OperationBot):
        """Fill events and eventsArchive with data from JSON."""
        # Import
        try:
            try:
                with open(cfg.JSON_FILEPATH) as jsonFile:
                    data = json.load(jsonFile)
            except json.decoder.JSONDecodeError:
                print("Malformed JSON file! Backing up and",
                      "creating an empty database")
                # Backup old file
                backupName = "{}-{}.bak" \
                    .format(cfg.JSON_FILEPATH,
                            datetime.now().strftime(
                                '%Y-%m-%dT%H-%M-%S'))
                os.rename(cfg.JSON_FILEPATH, backupName)
                print("Backed up to", backupName)
                # Let next handler create the file and continue importing
                raise FileNotFoundError
        except FileNotFoundError:
            print("JSON not found, creating")
            with open(cfg.JSON_FILEPATH, "w") as jsonFile:
                # Create a new file with empty JSON structure inside
                json.dump({"version": DATABASE_VERSION, "nextID": 0,
                           "events": {}, "eventsArchive": {}},
                          jsonFile, indent=2)
            # Try to import again
            await EventDatabase.fromJson(bot)
            return

        databaseVersion: int = int(data.get('version', 0))
        if databaseVersion != DATABASE_VERSION:
            msg = "Incorrect database version. Expected: {}, got: {}." \
                  .format(DATABASE_VERSION, databaseVersion)
            print(msg)
            await bot.commandchannel.send(msg)
            await bot.logout()

        EventDatabase.events = {}
        EventDatabase.eventsArchive = {}
        EventDatabase.nextID = data['nextID']
        eventsData = data['events']
        eventsArchiveData = data['eventsArchive']
        eventchannel = bot.eventchannel

        # Clear events channel
        if cfg.PURGE_ON_CONNECT:
            await eventchannel.purge(limit=100)

        # Add events
        for eventID, eventData in eventsData.items():
            # Create event
            date = datetime.strptime(eventData['date'],
                                     '%Y-%m-%d')
            eventMessage, event = \
                await EventDatabase.createEvent(date, eventchannel,
                                                importing=True)
            event.fromJson(eventID, eventData, eventchannel.guild)
            await EventDatabase.updateEvent(eventMessage, event)

        # Add reactions to events
        for event in EventDatabase.events.values():
            eventmessage: Message = await getEventMessage(bot, event)
            reactions = event.getReactions()
            await EventDatabase.updateReactions(eventmessage, reactions,
                                                bot.user)

        # Add archived events
        for eventID, eventData in eventsArchiveData.items():
            # Create event
            date = datetime.strptime(eventData['date'], "%Y-%m-%d")
            event = Event(date, eventchannel.guild.emojis)
            event.fromJson(eventID, eventData, eventchannel.guild)
            EventDatabase.eventsArchive[eventID] = event
            # TODO: test
            # EventDatabase.eventsArchive[int(eventID)] = event

        for eventID, event in EventDatabase.events.items():
            print(eventID, event)
