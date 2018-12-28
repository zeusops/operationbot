#!/usr/bin/env python3.7
import discord
import asyncio
import sqlite3

from discord.ext import commands
import config as cfg

initial_extensions = ['commandListener','event', "role"]

bot = commands.Bot(command_prefix=('!'))
bot.pm_help = True
bot.owner_ID = ('102170338942517248')

bot.remove_command("help")

if __name__ == '__main__':
    for extension in initial_extensions:
        # try:
            bot.load_extension(extension)
        # except Exception as e:
        #     print(f'failed to load extension {extension}')

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    await bot.change_presence(activity=discord.Game(name="Terry Big Gay", type=2))

bot.run(cfg.TOKEN)
