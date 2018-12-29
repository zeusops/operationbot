#!/usr/bin/env python3.7
import discord
from discord.ext import commands
import eventDatabase
import config as cfg
from secret import TOKEN, COMMAND_CHAR

CONFIG_VERSION = 4
if cfg.VERSION != CONFIG_VERSION:
    raise Exception(
        "Outdated config file, expecting version {}, found version {}"
        .format(CONFIG_VERSION, cfg.VERSION))

initial_extensions = ['commandListener', 'eventListener']

bot = commands.Bot(command_prefix=COMMAND_CHAR)
bot.remove_command("help")

eventDatabase = eventDatabase.EventDatabase()


@bot.event
async def on_ready():
    await bot.wait_until_ready()
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    await bot.change_presence(activity=discord.Game(name=cfg.GAME, type=2))


if __name__ == '__main__':
    bot.load_extension('reload')
    for extension in initial_extensions:
        # try:
            bot.load_extension(extension)
        # except Exception as e:
        #     print(f'failed to load extension {extension}')

    bot.run(TOKEN)
