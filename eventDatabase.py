import json
import os
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from discord import Emoji

import config as cfg
from event import Event

DATABASE_VERSION = 3


class EventDatabase:
    """Represents a database containing current events."""

    events: Dict[int, Event] = {}
    eventsArchive: Dict[int, Event] = {}
    nextID: int = 0

    @staticmethod
    def createEvent(date: datetime, emojis: Tuple[Emoji], eventID: int = -1,
                    sideop=False) -> Event:
        """Create a new event and store it.

        Does not create a message for the event.
        """
        if eventID == -1:
            eventID = EventDatabase.nextID
            EventDatabase.nextID += 1
            importing = False
        else:
            importing = True

        # Create event
        event = Event(date, emojis, eventID=eventID, importing=importing,
                      sideop=sideop)

        # Store event
        EventDatabase.events[eventID] = event

        return event

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
    def fromJson(emojis: Tuple[Emoji]):
        """Fill events and eventsArchive with data from JSON."""
        print("Importing")

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
            EventDatabase.fromJson(emojis)
            return

        databaseVersion: int = int(data.get('version', 0))
        if databaseVersion != DATABASE_VERSION:
            msg = "Incorrect database version. Expected: {}, got: {}." \
                  .format(DATABASE_VERSION, databaseVersion)
            print(msg)
            raise ValueError(msg)

        EventDatabase.events = {}
        EventDatabase.eventsArchive = {}
        EventDatabase.nextID = data['nextID']
        eventsData: Dict[str, Any] = data['events']
        eventsArchiveData = data['eventsArchive']

        # Add events
        for eventID, eventData in [
                (int(_id), _data)
                for _id, _data in eventsData.items()]:
            # Create event
            date = datetime.strptime(eventData['date'],
                                     '%Y-%m-%d')
            event = EventDatabase.createEvent(date, emojis, eventID=eventID)
            event.fromJson(eventID, eventData, emojis)
            EventDatabase.events[event.id] = event

        # Add archived events
        for eventID, eventData in eventsArchiveData.items():
            # Create event
            eventID = int(eventID)
            date = datetime.strptime(eventData['date'], "%Y-%m-%d")
            event = Event(date, emojis)
            event.fromJson(eventID, eventData, emojis)
            EventDatabase.eventsArchive[eventID] = event

        for eventID, event in EventDatabase.events.items():
            print(eventID, event)

        print("Import done")
