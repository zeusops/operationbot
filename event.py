import discord
import role
import roleGroup
import config as cfg


class Event:

    def __init__(self, date, guildEmojis):
        self.title = "Operation"
        self.date = date
        self.time = "18:45"
        self.terrain = " unknown"
        self.faction = " unknown"
        self.color = 0xFF4500
        self.roleGroups = {}
        self.additionalRoleCount = 0

        self.normalEmojis = self.getNormalEmojis(guildEmojis)
        self.addDefaultRoleGroups()
        self.addDefaultRoles()

    # Return an embed for the event
    def createEmbed(self):
        eventEmbed = discord.Embed(title=self.title + " (" + self.date + " - "
                                   + self.time + ")", description="Terrain:"
                                   + self.terrain + " - Faction:"
                                   + self.faction, colour=self.color)

        # Add field to embed for every rolegroup
        for group in self.roleGroups.values():
            if len(group.roles) > 0:
                eventEmbed.add_field(name=group.name, value=str(group),
                                     inline=group.isInline)

        return eventEmbed

    # Add default role groups
    def addDefaultRoleGroups(self):
        companyGroup = roleGroup.RoleGroup("Company", False)
        platoonGroup = roleGroup.RoleGroup("Platoon", True)
        alphaGroup = roleGroup.RoleGroup("Alpha", True)
        bravoGroup = roleGroup.RoleGroup("Bravo", True)
        additionalGroup = roleGroup.RoleGroup("Additional", True)

        self.roleGroups["Company"] = companyGroup
        self.roleGroups["Platoon"] = platoonGroup
        self.roleGroups["Alpha"] = alphaGroup
        self.roleGroups["Bravo"] = bravoGroup
        self.roleGroups["Additional"] = additionalGroup

    # Add default roles
    def addDefaultRoles(self):
        for name, groupName in cfg.DEFAULT_ROLES.items():
            # Only add role if the group exists
            if groupName in self.roleGroups.keys():
                emoji = self.normalEmojis[name]
                newRole = role.Role(name, emoji, False)
                self.roleGroups[groupName].addRole(newRole)

    # Add an additional role to the event
    def addAdditionalRole(self, name):
        # Find next emoji for additional role
        emoji = cfg.ADDITIONAL_ROLE_EMOJIS[self.additionalRoleCount]

        # Create role
        newRole = role.Role(name, emoji, True)

        # Add role to additional roles
        self.roleGroups["Additional"].addRole(newRole)
        self.additionalRoleCount += 1

        return emoji

    # Remove an additional role from the event
    def removeAdditionalRole(self, role_):
        # Remove role from additional roles
        self.roleGroups["Additional"].removeRole(role_)

        # Reorder the emotes of all the additional roles
        self.additionalRoleCount = 0
        for roleInstance in self.roleGroups["Additional"].roles:
            emoji = cfg.ADDITIONAL_ROLE_EMOJIS[self.additionalRoleCount]
            roleInstance.emoji = emoji
            self.additionalRoleCount += 1

    # Title setter
    def setTitle(self, newTitle):
        self.title = newTitle

    # Date setter
    def setDate(self, newDate):
        self.date = newDate

    # Time setter
    def setTime(self, newTime):
        self.time = newTime

    # Terrain setter
    def setTerrain(self, newTerrain):
        self.terrain = newTerrain

    # Faction setter
    def setFaction(self, newFaction):
        self.faction = newFaction

    # Get emojis for normal roles
    def getNormalEmojis(self, guildEmojis):
        normalEmojis = {}

        for emoji in guildEmojis:
            if emoji.name in cfg.DEFAULT_ROLES:
                normalEmojis[emoji.name] = emoji

        return normalEmojis

    # Returns reactions of all roles
    def getReactions(self):
        reactions = []

        for roleGroup_ in self.roleGroups.values():
            for role_ in roleGroup_.roles:
                reactions.append(role_.emoji)

        return reactions

    def getReactionsOfGroup(self, groupName):
        reactions = []

        if groupName in self.roleGroups.keys():
            for role_ in self.roleGroups[groupName].roles:
                reactions.append(role_.emoji)

        return reactions

    # Find role with emoji
    def findRole(self, emoji):
        for roleGroup_ in self.roleGroups.values():
            for role_ in roleGroup_.roles:
                if role_.emoji == emoji:
                    return role_

    # Add username to role
    def signup(self, roleToSet, username):
        for roleGroup_ in self.roleGroups.values():
            for role_ in roleGroup_.roles:
                if role_ == roleToSet:
                    role_.user = username

    # Remove username from any signups
    def undoSignup(self, username):
        for roleGroup_ in self.roleGroups.values():
            for role_ in roleGroup_.roles:
                if role_.user == username:
                    role_.user = ""
                    return role_.emoji
        return None

    # Returns if given user is already signed up
    def findSignup(self, username):
        for roleGroup_ in self.roleGroups.values():
            for role_ in roleGroup_.roles:
                if role_.user == username:
                    return role_
        return None

    def __str__(self):
        return "{} at {}".format(self.title, self.date)
