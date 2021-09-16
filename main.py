#!/usr/bin/env python3
import sys

import discord

import config as cfg
from operationbot import OperationBot
from secret import COMMAND_CHAR, TOKEN

CONFIG_VERSION = 9
if cfg.VERSION != CONFIG_VERSION:
    raise Exception(
        "Incompatible config file, expecting version {}, found version {}"
        .format(CONFIG_VERSION, cfg.VERSION))

initial_extensions = ['commandListener', 'eventListener', 'cogs.repl']

intents = discord.Intents.default()
intents.members = True
bot = OperationBot(command_prefix=COMMAND_CHAR, intents=intents)
# bot.remove_command("help")

if sys.version_info < (3, 9):
    raise Exception("Must be run with Python 3.9 or higher")

if __name__ == '__main__':
    print("Starting up")
    bot.load_extension('reload')
    print("Loading extensions")
    for extension in initial_extensions:
        # try:
        bot.load_extension(extension)
        # except Exception:
        #     print(f'failed to load extension {extension}')
    print("Running")
    bot.run(TOKEN)
