#!/usr/bin/env python3
import logging
import sys

import discord

from operationbot import config as cfg
from operationbot import secret as s
from operationbot.bot import OperationBot
from operationbot.secret import COMMAND_CHAR, TOKEN

CONFIG_VERSION = 15
SECRET_VERSION = 1
if cfg.VERSION != CONFIG_VERSION:
    raise ValueError(
        f"Incompatible config file, expecting version {CONFIG_VERSION}, "
        f"found version {cfg.VERSION}"
    )
if s.VERSION != SECRET_VERSION:
    raise ValueError(
        f"Incompatible secrets file, expecting version {SECRET_VERSION}, "
        f"found version {s.VERSION}"
    )

initial_extensions = [
    "operationbot.commandListener",
    "operationbot.eventListener",
    "operationbot.cogs.repl",
]

intents = discord.Intents.default()
intents.members = True  # pylint: disable=assigning-non-slot
intents.messages = True  # pylint: disable=assigning-non-slot
bot = OperationBot(command_prefix=COMMAND_CHAR, intents=intents)
# bot.remove_command("help")

if sys.version_info < (3, 10):
    raise Exception("Must be run with Python 3.10 or higher")


def main():
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("discord").setLevel(logging.INFO)
    logging.getLogger("discord.gateway").setLevel(logging.WARNING)
    print("Starting up")
    bot.load_extension("operationbot.reload")
    print("Loading extensions")
    for extension in initial_extensions:
        # try:
        bot.load_extension(extension)
        # except Exception:
        #     print(f'failed to load extension {extension}')
    print("Running")
    bot.run(TOKEN)
