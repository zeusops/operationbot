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

        platoonRoles = "HQ1PLT: \nRTO: \nFAC: " #str(normalEmojis[2]) + 
        alphaRoles = "ASL: \nA1: \nA2 "
        bravoRoles = "BSL: \nB1: \nB2: "

        eventEmbed.add_field(name="Platoon Roles", value=platoonRoles, inline=True) #TODO: Add role specific emotes to fields
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
        normalEmojis = []

        for emoteName in self.NORMAL_ROLE_EMOTE_NAMES:
            for emoji in guildEmojis:
                if (emoji.name == emoteName):
                    normalEmojis.append(emoji)
                    break
            
        return normalEmojis