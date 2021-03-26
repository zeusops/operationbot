import json
import os
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from discord import Emoji

import config as cfg
from event import Event
from errors import EventNotFound

DATABASE_VERSION = 4


class EventDatabase:
    """Represents a database containing current events."""

    events: Dict[int, Event] = {}
    eventsArchive: Dict[int, Event] = {}
    nextID: int = 0
    emojis: Optional[Tuple[Emoji]] = None

    @staticmethod
    def createEvent(date: datetime, emojis: Tuple[Emoji], eventID: int = -1,
                    sideop=False, platoon_size=None) -> Event:
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
                      sideop=sideop, platoon_size=platoon_size)

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
        EventDatabase.toJson(archive=False)
        EventDatabase.toJson(archive=True)

    @staticmethod
    def removeEvent(eventID: int, archived=False) -> Optional[Event]:
        """
        Remove event.

        Does not remove the message associated with the event.
        """
        events = EventDatabase.events if not archived \
                else EventDatabase.eventsArchive
        return events.pop(eventID, None)

    # was: findEvent
    @staticmethod
    def getEventByMessage(messageID: int, archived=False) -> Event:
        """Finds an event with its message ID.

        Raises EventNotFound if event cannot be found"""
        if archived:
            collection = EventDatabase.eventsArchive
        else:
            collection = EventDatabase.events

        for event in collection.values():
            if event.messageID == messageID:
                return event
        raise EventNotFound("No event found with message ID "
                            .format(messageID))

    @staticmethod
    def getEventByID(eventID: int, archived=False) -> Event:
        """Finds an event with its ID.

        Raises EventNotFound if event cannot be found."""
        if archived:
            collection = EventDatabase.eventsArchive
        else:
            collection = EventDatabase.events

        try:
            return collection[eventID]
        except KeyError:
            raise EventNotFound("No event found with ID {}".format(eventID))

    @staticmethod
    def getArchivedEventByMessage(messageID: int) -> Event:
        """Finds an archived event with its message ID.

        Raises EventNotFound if event cannot be found"""

        return EventDatabase.getEventByMessage(messageID, archived=True)

    # was: findEventInArchiveeventid
    @staticmethod
    def getArchivedEventByID(eventID: int):
        """Finds an archived event with its ID.

        Raises EventNotFound if event cannot be found."""
        return EventDatabase.getEventByID(eventID, archived=True)

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
        EventDatabase.events = {}
        for event in sortedEvents:
            # event = sortedEvents[index]
            event.messageID = messageIDs.pop()
            EventDatabase.events[event.id] = event

    @staticmethod
    def toJson(archive=False):
        # TODO: rename to saveDatabase
        events = EventDatabase.events if not archive \
                else EventDatabase.eventsArchive
        filename = cfg.JSON_FILEPATH['events' if not archive else 'archive']

        EventDatabase.writeJson(events, filename)

    @staticmethod
    def writeJson(events: Dict[int, Event], filename: str):
        # Get eventsData
        eventsData = {}
        for messageID, event in events.items():
            eventsData[messageID] = event.toJson()

        # Store data and return
        data: Dict[str, Any] = {}
        data['version'] = DATABASE_VERSION
        data['nextID'] = EventDatabase.nextID
        data['events'] = eventsData

        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as jsonFile:
            json.dump(data, jsonFile, indent=2)

    @staticmethod
    def loadDatabase(emojis: Optional[Tuple[Emoji]] = None):
        if EventDatabase.emojis is None:
            EventDatabase.emojis = emojis
        print("import events")
        EventDatabase.events, EventDatabase.nextID = \
            EventDatabase.readJson(cfg.JSON_FILEPATH['events'])
        print("import archive")
        EventDatabase.eventsArchive, _ = \
            EventDatabase.readJson(cfg.JSON_FILEPATH['archive'])

    @staticmethod
    def readJson(filename: str) -> Tuple[Dict[int, Event], int]:
        """Fill events and eventsArchive with data from JSON."""
        print("Importing")

        emojis = EventDatabase.emojis
        if emojis is None:
            raise ValueError("No EventDatabase.emojis set")

        # Import events
        try:
            try:
                with open(filename) as jsonFile:
                    data: Dict = json.load(jsonFile)
            except json.decoder.JSONDecodeError:
                print("Malformed JSON file! Backing up and",
                      "creating an empty database")
                # Backup old file
                backupName = "{}-{}.bak" \
                    .format(filename,
                            datetime.now().strftime('%Y-%m-%dT%H-%M-%S'))
                os.rename(filename, backupName)
                print("Backed up to", backupName)
                # Let next handler create the file and continue importing
                raise FileNotFoundError
        except FileNotFoundError:
            print("JSON not found, creating")
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, "w") as jsonFile:
                # Create a new file with empty JSON structure inside
                json.dump({
                    "version": DATABASE_VERSION,
                    "nextID": 0,
                    "events": {},
                }, jsonFile, indent=2)
            # Try to import again
            return EventDatabase.readJson(filename)

        databaseVersion = int(data.get('version', 0))
        if databaseVersion != DATABASE_VERSION:
            msg = "Incorrect database version. Expected: {}, got: {}." \
                  .format(DATABASE_VERSION, databaseVersion)
            print(msg)
            raise ValueError(msg)

        events = {}
        nextID = data['nextID']
        eventsData: Dict[str, Any] = data['events']

        # Add events
        for eventID, eventData in [
                (int(_id), _data)
                for _id, _data in eventsData.items()]:
            # Create event
            date = datetime.strptime(eventData['date'],
                                     '%Y-%m-%d')
            event = Event(date, emojis, importing=True)
            event.fromJson(eventID, eventData, emojis)
            events[event.id] = event

        for eventID, event in events.items():
            print(eventID, event)

        print("Import done")
        return events, nextID
