import json
import os
from datetime import datetime, date
from typing import Any, Dict, Optional, Tuple

from discord import Emoji

from operationbot import config as cfg
from operationbot.errors import EventNotFound
from operationbot.event import Event

DATABASE_VERSION = 4


class EventDatabase:
    """Represents a database containing current events."""

    events: Dict[int, Event] = {}
    eventsArchive: Dict[int, Event] = {}
    nextID: int = 0
    _emojis: Optional[Tuple[Emoji, ...]] = None

    # FIXME: class properties will be deprecated in Python 3.11,
    # find an alternative
    @classmethod  # type: ignore
    @property
    def emojis(cls) -> Tuple[Emoji, ...]:
        if cls._emojis is None:
            raise ValueError("No EventDatabase.emojis set")
        return cls._emojis

    @classmethod
    def createEvent(
        cls, event_date: datetime, eventID: int = -1, sideop=False, platoon_size=None
    ) -> Event:
        """Create a new event and store it.

        Does not create a message for the event.
        """
        if eventID == -1:
            eventID = cls.nextID
            cls.nextID += 1
            importing = False
        else:
            importing = True

        # Create event
        event = Event(
            event_date,
            cls.emojis,  # type: ignore
            eventID=eventID,
            importing=importing,
            sideop=sideop,
            platoon_size=platoon_size,
        )

        # Store event
        cls.events[eventID] = event

        return event

    @classmethod
    def archiveEvent(cls, event: Event):
        """
        Move event to archive.

        Does not remove or create messages.
        """
        # Remove event from events
        cls.removeEvent(event.id)

        # Add event to eventsArchive
        cls.eventsArchive[event.id] = event
        cls.toJson(archive=False)
        cls.toJson(archive=True)

    @classmethod
    def removeEvent(cls, eventID: int, archived=False) -> Optional[Event]:
        """
        Remove event.

        Does not remove the message associated with the event.
        """
        events = cls.events if not archived else cls.eventsArchive
        return events.pop(eventID, None)

    # was: findEvent
    @classmethod
    def getEventByMessage(cls, messageID: int, archived=False) -> Event:
        """Finds an event with its message ID.

        Raises EventNotFound if event cannot be found"""
        if archived:
            collection = cls.eventsArchive
        else:
            collection = cls.events

        for event in collection.values():
            if event.messageID == messageID:
                return event
        raise EventNotFound(f"No event found with message ID {messageID}")

    @classmethod
    def get_event_by_date(cls, event_date: date, archived=False) -> Event:
        """Find an event based on its date.

        Raises EventNotFound if an event cannot be found and ValueError if
        there are multiple events on the same date.
        """
        if archived:
            collection = cls.eventsArchive
        else:
            collection = cls.events

        events = list(
            filter(lambda event: event.date.date() == event_date, collection.values())
        )

        if len(events) == 0:
            raise EventNotFound(f"No event found on date {event_date}")
        if len(events) > 1:
            raise ValueError(
                f"Multiple events found on date {event_date}:\n"
                + "\n".join(str(event) for event in events)
            )
        return events[0]

    @classmethod
    def getEventByID(cls, eventID: int, archived=False) -> Event:
        """Finds an event with its ID.

        Raises EventNotFound if event cannot be found."""
        if archived:
            collection = cls.eventsArchive
        else:
            collection = cls.events

        try:
            return collection[eventID]
        except KeyError as e:
            raise EventNotFound(f"No event found with ID {eventID}") from e

    @classmethod
    def getArchivedEventByMessage(cls, messageID: int) -> Event:
        """Finds an archived event with its message ID.

        Raises EventNotFound if event cannot be found"""

        return cls.getEventByMessage(messageID, archived=True)

    # was: findEventInArchiveeventid
    @classmethod
    def getArchivedEventByID(cls, eventID: int):
        """Finds an archived event with its ID.

        Raises EventNotFound if event cannot be found."""
        return cls.getEventByID(eventID, archived=True)

    @classmethod
    def sortEvents(cls):
        sortedEvents: list[Event] = []
        messageIDs: list[int] = []

        # Store existing events
        for event in cls.events.values():
            sortedEvents.append(event)
            messageIDs.append(event.messageID)

        # Sort events based on date and time
        sortedEvents.sort(key=lambda event: event.date, reverse=True)
        messageIDs.sort(reverse=True)

        # Fill events again
        cls.events = {}
        for event in sortedEvents:
            # event = sortedEvents[index]
            new_id = messageIDs.pop()
            if new_id != event.messageID:
                event.messageID = new_id
                # If the message ID has changed, the new message needs a new
                # embed
                event.embed_hash = ""
            cls.events[event.id] = event

    @classmethod
    def toJson(cls, archive=False):
        # TODO: rename to saveDatabase
        events = cls.events if not archive else cls.eventsArchive
        filename = cfg.JSON_FILEPATH["events" if not archive else "archive"]

        cls.writeJson(events, filename)

    @classmethod
    def writeJson(cls, events: Dict[int, Event], filename: str):
        # Get eventsData
        eventsData = {}
        for messageID, event in events.items():
            eventsData[messageID] = event.toJson()

        # Store data and return
        data: Dict[str, Any] = {}
        data["version"] = DATABASE_VERSION
        data["nextID"] = cls.nextID
        data["events"] = eventsData

        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as jsonFile:
            json.dump(data, jsonFile, indent=2)

    @classmethod
    def loadDatabase(cls, emojis: Optional[Tuple[Emoji, ...]] = None):
        if cls._emojis is None:
            if emojis is None:
                raise ValueError("No emojis provided")
            cls._emojis = emojis
        print("Importing events")
        cls.events, cls.nextID = cls.readJson(cfg.JSON_FILEPATH["events"])
        print("Importing archive")
        cls.eventsArchive, _ = cls.readJson(
            cfg.JSON_FILEPATH["archive"], output_events=False
        )

    @classmethod
    def readJson(
        cls, filename: str, output_events=True
    ) -> Tuple[Dict[int, Event], int]:
        """Fill events and eventsArchive with data from JSON."""
        print("Importing")

        # Try to access emojis early so that we immediately bail out on error
        # We don't need to touch the database file if emojis is not set
        emojis = cls.emojis

        # Import events
        try:
            try:
                with open(filename) as jsonFile:
                    data: Dict = json.load(jsonFile)
            except json.decoder.JSONDecodeError as e:
                print("Malformed JSON file! Backing up and creating an empty database")
                backup_date = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
                # Backup old file
                backupName = f"{filename}-{backup_date}.bak"
                os.rename(filename, backupName)
                print("Backed up to", backupName)
                # Let next handler create the file and continue importing
                raise FileNotFoundError from e
        except FileNotFoundError:
            print("JSON not found, creating")
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, "w") as jsonFile:
                # Create a new file with empty JSON structure inside
                json.dump(
                    {
                        "version": DATABASE_VERSION,
                        "nextID": 0,
                        "events": {},
                    },
                    jsonFile,
                    indent=2,
                )
            # Try to import again
            return cls.readJson(filename)

        databaseVersion = int(data.get("version", 0))
        if databaseVersion != DATABASE_VERSION:
            msg = (
                "Incorrect database version. Expected: "
                f"{DATABASE_VERSION}, got: {databaseVersion}."
            )
            print(msg)
            raise ValueError(msg)

        events = {}
        nextID = data["nextID"]
        eventsData: Dict[str, Any] = data["events"]

        # Add events
        for eventID, eventData in [
            (int(_id), _data) for _id, _data in eventsData.items()
        ]:
            # Create event
            event_date = datetime.strptime(eventData["date"], "%Y-%m-%d")
            # NOTE: Ignoring the type here because mypy is buggy and doesn't
            # detect class properties correctly
            event = Event(event_date, emojis, importing=True)  # type: ignore
            event.fromJson(eventID, eventData, emojis)
            events[event.id] = event

        if output_events:
            for eventID, event in events.items():
                print(eventID, event)

        print("Import done")
        return events, nextID
