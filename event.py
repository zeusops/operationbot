import discord
import sqlite3
import role

from discord.ext import commands

class Event:

    def __init__(self, title, date, color, guildEmojis):
        self.title = title
        self.date = date
        self.color = color
        self.additionalRoles = []

        self.ADDITIONAL_ROLE_EMOTES = [
            ":one:",
            ":two:",
            ":three:",
            ":four:",
            ":five:",
            ":six:",
            ":seven:",
            ":eight:",
            ":nine:",
            ":zero:"
        ]

        self.NORMAL_ROLE_EMOTE_NAMES = [
            "ZEUS",
            "MOD",
            "HQ",
            "RTO",
            "FAC",
            "ASL",
            "A1",
            "A2",
            "BSL",
            "B1",
            "B2"
        ]

        self.normalEmojis = self.getNormalEmojis(guildEmojis)
    
    # Return an embed for the event
    def createEmbed(self, date):
        eventEmbed = discord.Embed(title=("Operation"), description="(" + str(date) + ")", colour=0xFF4500)

        enter = "\n"
        platoonRoles = str(normalEmojis["HQ"]) + enter + str(normalEmojis["RTO"]) + enter + str(normalEmojis["FAC"])
        alphaRoles = str(normalEmojis["ASL"]) + enter + str(normalEmojis["A1"]) + enter + str(normalEmojis["A2"])
        bravoRoles = str(normalEmojis["BSL"]) + enter + str(normalEmojis["B1"]) + enter + str(normalEmojis["B2"])

        eventEmbed.add_field(name="Platoon Roles", value=platoonRoles, inline=True)
        eventEmbed.add_field(name="Alpha Leading Roles", value=alphaRoles, inline=True)
        eventEmbed.add_field(name="Bravo Leading Roles", value=bravoRoles, inline=True)

        return eventEmbed

    # Add an additional role to the event
    def addRole(self, name):
        # Find next emote for additional role
        emote = self.ADDITIONAL_ROLE_EMOTES[len(self.additionalRoles)]

        newRole = role.Role(name, emote)

        self.additionalRoles.append(newRole)

    # Get emojis for normal roles
    def getNormalEmojis(self, guildEmojis):
        normalEmojis = {}

        for emoteName in self.NORMAL_ROLE_EMOTE_NAMES:
            for emoji in guildEmojis:
                if (emoji.name == emoteName):
                    normalEmojis[emoteName] = emoji
                    break
            
        return normalEmojis