from datetime import datetime, timedelta, timezone
from typing import Any

from discord import Emoji

from operationbot import config as cfg
from operationbot.event import Event
from operationbot.eventDatabase import EventDatabase as db
from operationbot.role import Role
from operationbot.roleGroup import RoleGroup


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


def test_cancel_empty():
    _init_db()

    class _Role(Role):
        next_uid = 0

        def __init__(self, name: str, emoji: str | Emoji, show_name: bool = False):
            self.name = name
            self.userID: int | None = None
            self.userName = ""
            self.emoji = cfg.ADDITIONAL_ROLE_EMOJIS[0]

        def signup(self):
            self.userID = _Role.next_uid
            _Role.next_uid += 1
            self.userName = f"User {self.userID}"

        def toJson(self, brief_output=False) -> dict[str, Any]:
            return {}

    def _init_event(event: Event, signup=False) -> None:
        group = event.roleGroups.get("Company")
        if not group:
            group = RoleGroup("Company")
            event.roleGroups["Company"] = group
        role = _Role("ZEUS", ":zeus:")
        group.addRole(role)
        if signup:
            role.signup()

    date_close = datetime.now() + timedelta(hours=1)
    date_far = datetime.now() + timedelta(hours=3)

    event_close = db.createEvent(date_close, platoon_size="empty")
    event_close.title = "close"
    event_far = db.createEvent(date_far, platoon_size="empty")
    event_far.title = "far"
    event_close_empty = db.createEvent(
        date_close + timedelta(minutes=1), platoon_size="empty"
    )
    event_close_empty.title = "close empty"
    event_far_empty = db.createEvent(
        date_far + timedelta(minutes=1), platoon_size="empty"
    )
    event_far_empty.title = "far empty"

    _init_event(event_close, signup=True)
    _init_event(event_far, signup=True)
    _init_event(event_close_empty)
    _init_event(event_far_empty)

    # print(event_close.roleGroups)

    assert not event_close.is_empty()
    assert not event_far.is_empty()
    assert event_close_empty.is_empty()
    assert event_far_empty.is_empty()

    assert len(db.events) == 4
    assert len(db.eventsArchive) == 0
    events = db.cancel_empty_events(timedelta(hours=2))
    assert len(events) == 1
    assert events[0].cancelled
    assert len(db.events) == 4
    events = db.cancel_empty_events(timedelta(hours=2))
    assert len(events) == 0
