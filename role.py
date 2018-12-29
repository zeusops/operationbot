import discord
import sqlite3

from discord.ext import commands

class Role:

    def __init__(self, name, emote):
        self.name = name
        self.emote = emote
        self.user = ""

    def setUser(self, user):
        self.user = user