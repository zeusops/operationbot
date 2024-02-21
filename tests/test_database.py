from datetime import datetime, time, timedelta, timezone
from typing import cast

from discord import Embed
from operationbot import config as cfg
from operationbot.event import Event
from operationbot.eventDatabase import EventDatabase as db


def _timestamp(date: datetime) -> int:
    return int(date.replace(tzinfo=cfg.TIME_ZONE).astimezone(timezone.utc).timestamp())


def _init_db() -> None:
    db.events = {}
    db.eventsArchive = {}
    db.nextID = 0
    db._emojis = ()
    cfg.DEFAULT_ROLES = {
        "empty": {},
    }


def test_archive_past():
    _init_db()

    date_past = datetime.now() - timedelta(hours=3)
    date_coming = datetime.now() + timedelta(hours=3)
    event_past = db.createEvent(date_past, platoon_size="empty")
    event_coming = db.createEvent(date_coming, platoon_size="empty")

    assert db.events.get(0) == event_past
    assert len(db.eventsArchive) == 0
    archived = db.archive_past_events()
    assert len(archived) == 1
    assert len(db.eventsArchive) == 1
    assert archived[0] == event_past
    assert db.events.get(0) != event_past
    assert db.events.get(1) == event_coming


def test_archive_past_delta():
    _init_db()

    date_past = datetime.now() - timedelta(hours=1)
    date_coming = datetime.now() + timedelta(hours=3)
    event_past = db.createEvent(date_past, platoon_size="empty")
    event_coming = db.createEvent(date_coming, platoon_size="empty")

    assert len(db.events) == 2
    assert db.events.get(0) == event_past
    assert len(db.eventsArchive) == 0
    archived = db.archive_past_events(timedelta(hours=2))
    assert len(archived) == 0
    assert len(db.eventsArchive) == 0
    assert db.events.get(0) == event_past
    assert db.events.get(1) == event_coming


def test_default():
    date = datetime(2020, 1, 1, 12, 0, 0)
    event = Event(date, (), platoon_size="empty")

    assert event.date == date
    assert event.time == time(hour=date.hour, minute=date.minute)
    date = datetime(2020, 1, 2, 12, 0, 0)
    event.date = date
    assert event.date == date

    event.faction = "USMC"
    assert event.faction == "USMC"

    event.terrain = "Stratis"
    assert event.terrain == "Stratis"

    assert event.title == "Operation"
    assert event.description == ""
    timestamp = _timestamp(date)
    # A non-cached embed will never be None, casting to make the linters happy
    embed = cast(Embed, event.createEmbed(cache=False))
    assert embed.description == (
        f"Local time: <t:{timestamp}> "
        f"(<t:{timestamp}:R>)"
        f"\nTerrain: Stratis - Faction: USMC"
    )


def test_dlc():
    date = datetime(2020, 1, 1, 12, 0, 0)
    event = Event(date, (), platoon_size="empty")

    event.terrain = "Tanoa"
    assert event.terrain == "Tanoa"
    assert event.faction == "unknown"
    assert event.title == "APEX Operation"
    assert event.description == ""
    timestamp = _timestamp(date)
    # A non-cached embed will never be None, casting to make the linters happy
    embed = cast(Embed, event.createEmbed(cache=False))
    assert embed.description == (
        f"Local time: <t:{timestamp}> "
        f"(<t:{timestamp}:R>)"
        f"\nTerrain: {event.terrain} - Faction: {event.faction}\n\n"
        f"The **{event.dlc} DLC** is required to join this event"
    )
    event.terrain = "Stratis"
    assert event.dlc is None
    event.dlc = "GlobMob"
    assert event.dlc == "GlobMob"
