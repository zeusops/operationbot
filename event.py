from datetime import datetime
from typing import Dict, Tuple

from discord import Embed, Emoji

import config as cfg
from role import Role
from roleGroup import RoleGroup


class Event:

    def __init__(self, date: datetime, guildEmojis: Tuple[Emoji]):
        self.title = "Operation"
        self.date = date
        self.terrain = "unknown"
        self.faction = "unknown"
        self.description = ""
        self.color = 0xFF4500
        self.roleGroups: Dict[str, RoleGroup] = {}
        self.additionalRoleCount = 0

        self.normalEmojis = self.getNormalEmojis(guildEmojis)
        self.addDefaultRoleGroups()
        self.addDefaultRoles()

    # Return an embed for the event
    def createEmbed(self) -> Embed:
        title = "{} ({})".format(
            self.title, self.date.strftime("%a %Y-%m-%d - %H:%M CEST"))
        description = "Terrain: {} - Faction: {}\n\n{}".format(
            self.terrain, self.faction, self.description)
        eventEmbed = Embed(title=title, description=description,
                           colour=self.color)

        # Add field to embed for every rolegroup
        for group in self.roleGroups.values():
            if len(group.roles) > 0:
                eventEmbed.add_field(name=group.name, value=str(group),
                                     inline=group.isInline)

        return eventEmbed

    # Add default role groups
    def addDefaultRoleGroups(self):
        companyGroup = RoleGroup("Company", False)
        platoonGroup = RoleGroup("Platoon", True)
        alphaGroup = RoleGroup("Alpha", True)
        bravoGroup = RoleGroup("Bravo", True)
        additionalGroup = RoleGroup("Additional", True)

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
                newRole = Role(name, emoji, False)
                self.roleGroups[groupName].addRole(newRole)

    # Add an additional role to the event
    def addAdditionalRole(self, name: str) -> str:
        # Find next emoji for additional role
        emoji = cfg.ADDITIONAL_ROLE_EMOJIS[self.additionalRoleCount]

        # Create role
        newRole = Role(name, emoji, True)

        # Add role to additional roles
        self.roleGroups["Additional"].addRole(newRole)
        self.additionalRoleCount += 1

        return emoji

    # Remove an additional role from the event
    def removeAdditionalRole(self, role: str):
        # Remove role from additional roles
        self.roleGroups["Additional"].removeRole(role)

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
        self.date = self.date.replace(year=newDate.year, month=newDate.month,
                                      day=newDate.day)

    # Time setter
    def setTime(self, newTime):
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

        for roleGroup in self.roleGroups.values():
            role: Role
            for role in roleGroup.roles:
                emoji = role.emoji
                # Skip the ZEUS reaction. Zeuses can only be signed up using
                # the signup command
                if not (isinstance(emoji, Emoji) and emoji.name == "ZEUS"):
                    reactions.append(role.emoji)

        return reactions

    def getReactionsOfGroup(self, groupName):
        reactions = []

        if groupName in self.roleGroups.keys():
            for role in self.roleGroups[groupName].roles:
                reactions.append(role.emoji)

        return reactions

    # Find role with emoji
    def findRoleWithEmoji(self, emoji) -> Role:
        for roleGroup in self.roleGroups.values():
            for role in roleGroup.roles:
                if role.emoji == emoji:
                    return role
        return None

    # Find role with name
    def findRoleWithName(self, roleName: str) -> Role:
        roleName = roleName.lower()
        for roleGroup in self.roleGroups.values():
            role: Role
            for role in roleGroup.roles:
                if role.name.lower() == roleName:
                    return role
        return None

    # Add username to role
    def signup(self, roleToSet, user):
        for roleGroup in self.roleGroups.values():
            for role in roleGroup.roles:
                if role == roleToSet:
                    role.userID = user.id
                    role.userName = user.display_name

    # Remove username from any signups
    def undoSignup(self, user) -> None:
        for roleGroup in self.roleGroups.values():
            for role in roleGroup.roles:
                if role.userID == user.id:
                    role.userID = None
                    role.userName = ""
        return None

    # Returns if given user is already signed up
    def findSignup(self, userID) -> Role:
        for roleGroup in self.roleGroups.values():
            for role in roleGroup.roles:
                if role.userID == int(userID):
                    return role
        return None

    def __str__(self):
        return "{} at {}".format(self.title, self.date)

    def toJson(self):
        roleGroupsData = {}
        for groupName, roleGroup in self.roleGroups.items():
            roleGroupsData[groupName] = roleGroup.toJson()

        data = {}
        data["title"] = self.title
        data["date"] = self.date.strftime("%Y-%m-%d")
        data["description"] = self.description
        data["time"] = self.date.strftime("%H:%M")
        data["terrain"] = self.terrain
        data["faction"] = self.faction
        data["color"] = self.color
        data["roleGroups"] = roleGroupsData
        return data

    def fromJson(self, data, guild):
        self.setTitle(data["title"])
        time = datetime.strptime(data["time"], "%H:%M")
        self.setTime(time)
        self.setTerrain(data["terrain"])
        self.faction = data["faction"]
        self.description = data.get("description", "")
        self.color = data["color"]
        for groupName, roleGroupData in data["roleGroups"].items():
            roleGroup = RoleGroup(groupName, False)
            roleGroup.fromJson(roleGroupData, guild)
            self.roleGroups[groupName] = roleGroup
