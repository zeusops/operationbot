from typing import List

from discord import Guild

import config as cfg
from role import Role


class RoleGroup:

    def __init__(self, name: str, isInline: bool = True):
        self.name = name
        self.isInline = isInline
        self.roles: List[Role] = []

    # Add role to the group
    def addRole(self, role: Role):
        self.roles.append(role)

    # Remove role from the group
    def removeRole(self, roleName: str):
        for role in self.roles:
            if (role.name == roleName):
                self.roles.remove(role)

    def __str__(self) -> str:
        roleGroupString = ""

        for role in self.roles:
            roleGroupString += str(role)

        return roleGroupString

    def toJson(self):
        rolesData = {}
        for role in self.roles:
            rolesData[role.name] = role.toJson()

        data = {}
        data["name"] = self.name
        data["isInline"] = self.isInline
        data["roles"] = rolesData
        return data

    def fromJson(self, data: dict, guild: Guild):
        self.name = data["name"]
        self.isInline = data["isInline"]
        for roleName, roleData in data["roles"].items():
            roleEmoji = None
            if (type(roleData["emoji"]) is str):
                for emoji in guild.emojis:
                    if emoji.name == roleData["emoji"]:
                        roleEmoji = emoji
                        break
            else:
                roleEmoji = cfg.ADDITIONAL_ROLE_EMOJIS[roleData["emoji"]]
            role = Role(roleData["name"], roleEmoji, roleData["displayName"])
            role.fromJson(roleData)
            self.roles.append(role)
