#!/usr/bin/env python3
from discord.ext.commands import Bot

import config as cfg
from secret import COMMAND_CHAR, TOKEN

CONFIG_VERSION = 5
if cfg.VERSION != CONFIG_VERSION:
    raise Exception(
        "Incompatible config file, expecting version {}, found version {}"
        .format(CONFIG_VERSION, cfg.VERSION))

initial_extensions = ['commandListener', 'eventListener']
bot = Bot(command_prefix=COMMAND_CHAR)
# bot.remove_command("help")

if __name__ == '__main__':
    bot.load_extension('reload')
    for extension in initial_extensions:
        # try:
        bot.load_extension(extension)
        # except Exception:
        #     print(f'failed to load extension {extension}')

    bot.run(TOKEN)
