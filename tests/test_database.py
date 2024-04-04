from datetime import datetime, timedelta, timezone

from operationbot import config as cfg
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
