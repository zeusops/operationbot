#!/usr/bin/env python3
import config as cfg
from operationbot import OperationBot
from secret import COMMAND_CHAR, TOKEN
import discord

CONFIG_VERSION = 8
if cfg.VERSION != CONFIG_VERSION:
    raise Exception(
        "Incompatible config file, expecting version {}, found version {}"
        .format(CONFIG_VERSION, cfg.VERSION))

initial_extensions = ['commandListener', 'eventListener', 'cogs.repl']
bot = OperationBot(command_prefix=COMMAND_CHAR, intents=discord.Intents.all())
# bot.remove_command("help")

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
