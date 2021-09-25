from typing import Any, Dict, List, Tuple, Union

from discord import Emoji

import config as cfg
from errors import RoleNotFound, UnexpectedRole
from role import Role


class RoleGroup:

    def __init__(self, name: str, isInline: bool = True):
        self.name = name
        self.isInline = isInline
        self.roles: List[Role] = []

    def __repr__(self):
        return f"<RoleGroup name='{self.name}'>"

    def __getitem__(self, key: str) -> Role:
        for role in self.roles:
            if role.name.lower() == key.lower():
                return role
        raise KeyError(key)

    def __len__(self) -> int:
        # Allows checking the number of roles with a plain len(roleGroup)
        return len(self.roles)

    def __setitem__(self, key, value):
        self.removeRole(key)
        self.addRole(value)

    # Add role to the group
    def addRole(self, role: Role):
        self.roles.append(role)

    # Remove role from the group
    def removeRole(self, role: Union[str, Role]) -> None:
        try:
            if isinstance(role, str):
                name = role
                role = self[role]
            else:
                name = role.name
            self.roles.remove(role)
        except (KeyError, ValueError) as e:
            raise RoleNotFound(f"Could not find a role named {name} to remove "
                               f"from group {self.name}") from e

    def __str__(self) -> str:
        roleGroupString = ""

        for role in self.roles:
            roleGroupString += f'{str(role)}\n'

        return roleGroupString

    def toJson(self, brief_output=False) -> Dict[str, Any]:
        rolesData = {}
        for role in self.roles:
            emoji: Union[int, str]
            if isinstance(role.emoji, str):
                emoji = cfg.ADDITIONAL_ROLE_EMOJIS.index(role.emoji)
            else:
                emoji = role.emoji.name
            rolesData[emoji] = role.toJson(brief_output=brief_output)

        data: Dict[str, Any] = {}
        data["name"] = self.name
        data["isInline"] = self.isInline
        data["roles"] = rolesData
        return data

    def fromJson(self, data: dict, emojis: Tuple[Emoji, ...],
                 manual_load=False):
        self.name = data["name"]
        if not manual_load:
            self.isInline = data["isInline"]

        roles: List[str] = []
        for roleEmoji, roleData in data["roles"].items():
            try:
                roleEmoji = cfg.ADDITIONAL_ROLE_EMOJIS[int(roleEmoji)]
            except ValueError:
                for emoji in emojis:
                    if emoji.name == roleEmoji:
                        roleEmoji = emoji
                        break
            if not manual_load:
                # Only create new roles if we're not loading data manually from
                # the command channel
                role = Role(roleData["name"], roleEmoji, self.name,
                            self.get_corrected_name(roleData))
                self.roles.append(role)
            else:
                try:
                    role = next(x for x in self.roles if x.emoji == roleEmoji)
                except StopIteration as e:
                    name = roleData.get("show_name") or roleData["name"]
                    raise UnexpectedRole(f"Cannot import unexpected role "
                                         f"'{name}'") from e
                roles.append(roleEmoji)

            role.fromJson(roleData, manual_load=manual_load)
        if manual_load:
            # Remove roles that were not present in imported data
            self.roles = [x for x in self.roles if x.emoji in roles]

    # TODO: this should be handled in EventDatabase instead based on the DB
    #       version
    def get_corrected_name(self, roleData: Dict[str, bool]) -> bool:
        if "displayName" in roleData:
            show_name = roleData["displayName"]
        else:
            show_name = roleData["show_name"]
        return show_name
