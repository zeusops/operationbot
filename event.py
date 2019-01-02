import datetime
import discord
import role
import roleGroup
import config as cfg


class Event:

    def __init__(self, date, guildEmojis):
        self.title = "Operation"
        self.date = datetime.datetime.strptime(date + " 18:45",
                                               "%Y-%m-%d %H:%M")
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
        eventEmbed = discord.Embed(title=self.title + " (" +
                                   self.date.strftime("%a %Y-%m-%d - %H:%M") +
                                   ")", description="Terrain:" + self.terrain +
                                   " - Faction:" + self.faction,
                                   colour=self.color)

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
                newRole = role.Role(" " + name, emoji, False)
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
    def setDate(self, newDateString):
        newDate = datetime.datetime.strptime(newDateString, "%Y-%m-%d")
        self.date = self.date.replace(year=newDate.year, month=newDate.month,
                                      day=newDate.day)

    # Time setter
    def setTime(self, newTimeString):
        newTime = datetime.datetime.strptime(newTimeString, "%H:%M")
        self.date = self.date.replace(hour=newTime.hour, minute=newTime.minute)

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
    def findRoleWithEmoji(self, emoji):
        for roleGroup_ in self.roleGroups.values():
            for role_ in roleGroup_.roles:
                if role_.emoji == emoji:
                    return role_
        return None

    # Find role with name
    def findRoleWithName(self, roleName):
        for roleGroup_ in self.roleGroups.values():
            for role_ in roleGroup_.roles:
                if role_.name == roleName:
                    return role_
        return None

    # Add username to role
    def signup(self, roleToSet, user):
        for roleGroup_ in self.roleGroups.values():
            for role_ in roleGroup_.roles:
                if role_ == roleToSet:
                    role_.userID = user.id
                    role_.userName = user.display_name

    # Remove username from any signups
    def undoSignup(self, user):
        for roleGroup_ in self.roleGroups.values():
            for role_ in roleGroup_.roles:
                if role_.userID == user.id:
                    role_.userID = None
                    role_.userName = ""
                    return role_.emoji
        return None

    # Returns if given user is already signed up
    def findSignup(self, userID):
        for roleGroup_ in self.roleGroups.values():
            for role_ in roleGroup_.roles:
                if role_.userID == int(userID):
                    return role_
        return None

    def __str__(self):
        return "{} at {}".format(self.title, self.date)

    def toJson(self):
        roleGroupsData = {}
        for groupName, roleGroup_ in self.roleGroups.items():
            roleGroupsData[groupName] = roleGroup_.toJson()

        data = {}
        data["title"] = self.title
        data["date"] = self.date.strftime("%Y-%m-%d")
        data["time"] = self.date.strftime("%H:%M")
        data["terrain"] = self.terrain
        data["faction"] = self.faction
        data["color"] = self.color
        data["roleGroups"] = roleGroupsData
        return data

    def fromJson(self, data, guild):
        self.setTitle(data["title"])
        self.setTime(data["time"])
        self.setTerrain(data["terrain"])
        self.faction = data["faction"]
        self.color = data["color"]
        for groupName, roleGroupData in data["roleGroups"].items():
            roleGroup_ = roleGroup.RoleGroup(groupName, False)
            roleGroup_.fromJson(roleGroupData, guild)
            self.roleGroups[groupName] = roleGroup_
