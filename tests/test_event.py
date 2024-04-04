from datetime import datetime, time, timezone
from typing import cast

from discord import Embed
from operationbot import config as cfg
from operationbot.event import Event


def _timestamp(date: datetime) -> int:
    return int(date.replace(tzinfo=cfg.TIME_ZONE).astimezone(timezone.utc).timestamp())


def test_default():
    date = datetime(2020, 1, 1, 12, 0, 0)
    event = Event(date, guildEmojis=(), platoon_size="empty")

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
    event = Event(date, guildEmojis=(), platoon_size="empty")

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
    assert event.dlc == ""
    event.dlc = "GlobMob"
    assert event.dlc == "GlobMob"


def test_manual_dlc():
    date = datetime(2020, 1, 1, 12, 0, 0)
    event = Event(date, guildEmojis=(), platoon_size="empty")
    event.dlc = "APEX"
    event.terrain = "Stratis"
    assert event.dlc == "APEX"
    assert event.terrain == "Stratis"
