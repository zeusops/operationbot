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
    def createEvent(date: datetime, emojis: Tuple[Emoji], eventID: int = -1) \
            -> Event:
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
        event = Event(date, emojis, eventID=eventID, importing=importing)

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
        EventDatabase.removeEvent(event)

        event.archived = True

        # Add event to eventsArchive
        EventDatabase.eventsArchive[event.id] = event

    @staticmethod
    def removeEvent(event: Event) -> bool:
        """
        Remove event.

        Does not remove the message associated with the event.
        """
        if event.archived:
            if event.id in EventDatabase.eventsArchive.keys():
                del EventDatabase.eventsArchive[event.id]
                return True
        else:
            if event.id in EventDatabase.events.keys():
                del EventDatabase.events[event.id]
                return True
        return False

    # was: findEvent
    @staticmethod
    def getEventByMessage(messageID: int, archived=False) -> Optional[Event]:
        """Find an event with it's message ID."""
        event: Event
        if archived:
            events = EventDatabase.eventsArchive
        else:
            events = EventDatabase.events

        for event in events.values():
            if event.messageID == messageID:
                return event
        return None

    @staticmethod
    def getEventByID(eventID: int, archived=False) -> Optional[Event]:
        """Find an event with it's ID."""
        if archived:
            return EventDatabase.eventsArchive.get(eventID)
        else:
            return EventDatabase.events.get(eventID)

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
        for eventID, eventData in eventsData.items():
            # Create event
            eventID = int(eventID)
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
