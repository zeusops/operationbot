from typing import List, Tuple

from discord import Emoji, Guild

import config as cfg
from role import Role


class RoleGroup:

    def __init__(self, name: str, isInline: bool = True):
        self.name = name
        self.isInline = isInline
        self.roles: List[Role] = []

    def __repr__(self):
        return "<RoleGroup name='{}'>".format(self.name)

    def __getitem__(self, key):
        for role in self.roles:
            if role.name == key:
                return role
        raise KeyError(key)

    def __setitem__(self, key, value):
        self.removeRole(key)
        self.addRole(value)

    # Add role to the group
    def addRole(self, role: Role):
        self.roles.append(role)

    # Remove role from the group
    def removeRole(self, roleName: str):
        for role in self.roles:
            if role.name == roleName:
                self.roles.remove(role)

    def __str__(self) -> str:
        roleGroupString = ""

        for role in self.roles:
            roleGroupString += str(role)

        return roleGroupString

    def toJson(self):
        rolesData = {}
        for role in self.roles:
            if type(role.emoji) is str:
                emoji = cfg.ADDITIONAL_ROLE_EMOJIS.index(role.emoji)
            else:
                emoji = role.emoji.name
            rolesData[emoji] = role.toJson()

        data = {}
        data["name"] = self.name
        data["isInline"] = self.isInline
        data["roles"] = rolesData
        return data

    def fromJson(self, data: dict, emojis: Tuple[Emoji]):
        self.name = data["name"]
        self.isInline = data["isInline"]
        for roleEmoji, roleData in data["roles"].items():
            try:
                roleEmoji = cfg.ADDITIONAL_ROLE_EMOJIS[int(roleEmoji)]
            except ValueError:
                for emoji in emojis:
                    if emoji.name == roleEmoji:
                        roleEmoji = emoji
                        break
            role = Role(roleData["name"], roleEmoji, roleData["displayName"])
            role.fromJson(roleData)
            self.roles.append(role)
