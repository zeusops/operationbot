"""A simple (if borked) OperationBot test.

Uses dpytest to mock the discord client code,
enabling simple enough tests to be written.

Currently tries to call the !create event command, see eventListener.py
limitations.

Intent is to show how a skeleton of testing can be added.

In true TDD fashion, the parts where test-writing chafes is parts that should be
investigated for over-coupling and other troubles.

In this case, writing this test posed a couple issues: - secrets.py imported by
config, imported by main bot, hard to mock - creating event needs to fetch all
previous event data from channel (hard to mock)

Uh, obviously, remember I know almost nothing about this codebase, except what I
dug in for a couple hours, I'm not claiming expertise (first time messing with
discord bot).

"""

import pytest
import discord.ext.test as dpytest
from discord import Intents

from operationbot import OperationBot

@pytest.fixture
def bot(event_loop):
    # Abridged version of main.py's invocation of bot class
    initial_extensions = ['commandListener', 'eventListener']
    intents = Intents.default()
    intents.members = True
    # Special sauce: including the test's event_loop as param
    bot = OperationBot(command_prefix="!", intents=intents, loop=event_loop)
    for extension in initial_extensions:
        bot.load_extension(extension)
    dpytest.configure(bot)
    return bot

# This test creates a throwaway bot instance using the bot() func above
@pytest.mark.asyncio
async def test_event_creation(bot, caplog):
    """Scenario: Creating an event from user message"""
    # Given an OperationBot
    # (captured by the bot parameter/function via pytest fixture)

    # Setting log capture to debug, to surface why 'ready' event won't go.
    import logging
    caplog.set_level(logging.DEBUG)

    # Mark the discord client as ready overall, calling EventListener.on_ready()
    # Note it doesn't complete checks of EventListener.wait_until_ready(), which
    # is a separate event/handler...
    dpytest.get_config().client._get_state().dispatch("ready")

    # All sorts of attempts at manually sending the 'ready' event to unblock
    # EventListener.wait_until_ready():
    # bot.cogs['EventListener'].dispatch("ready")
    # dpytest.get_config().client.get_cog("EventListener").dispatch("ready")

    # When I send message "!create 2025-01-01"
    await dpytest.message("!create 2025-01-01")

    # Then a message is posted containing "Created event"
    assert dpytest.verify().message().contains().content("Created event")
