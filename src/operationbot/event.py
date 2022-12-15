import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import discord
from discord import Embed, Emoji

from operationbot import config as cfg
from operationbot.additional_role_group import AdditionalRoleGroup
from operationbot.config import EMBED_COLOR
from operationbot.errors import RoleError, RoleGroupNotFound, RoleNotFound, RoleTaken
from operationbot.role import Role
from operationbot.roleGroup import RoleGroup
from operationbot.secret import PLATOON_SIZE

TITLE = "Operation"
SIDEOP_TITLE = "Side Operation"
TERRAIN = "unknown"
FACTION = "unknown"
DESCRIPTION = ""
MODS = ""
# Discord API limitation
MAX_REACTIONS = 20


class User:
    # This class implements the same signature as the discord.abc.User class,
    # we need to use the 'id' argument here.
    # pylint: disable=redefined-builtin
    def __init__(self, id: int = None, display_name: str = None):
        self.id = id
        self.display_name = display_name

    def __eq__(self, other: Union['User', discord.abc.User]):  # type: ignore
        # This makes it so that User objects can be compared to
        # discord.abc.User by doing `user == discord.abc.User`. The comparison
        # will not work in the other direction because discord.abc.User checks
        # for the object type.
        return self.id == other.id


class Event:

    def __init__(self, date: datetime.datetime, guildEmojis: Tuple[Emoji, ...],
                 eventID=0, importing=False, sideop=False, platoon_size=None):
        self._title: Optional[str] = None
        self.date = date
        self._terrain = TERRAIN
        self.faction = FACTION
        self.description = DESCRIPTION
        self.port = cfg.PORT_DEFAULT
        self.mods = MODS
        self.roleGroups: Dict[str, RoleGroup] = {}
        self.messageID = 0
        self.id = eventID
        self.sideop = sideop
        self.attendees: list[Union[User, discord.abc.User]] = []
        self.dlc: Optional[str] = None

        if platoon_size is None:
            if sideop:
                self.platoon_size = "sideop"
            else:
                self.platoon_size = PLATOON_SIZE
        elif platoon_size in cfg.DEFAULT_ROLES:
            self.platoon_size = platoon_size
        else:
            raise ValueError(f"Unsupported platoon size: {platoon_size}")

        if self.platoon_size.startswith("WW2"):
            self.title = "WW2 " + self.title

        self.normalEmojis = self._getNormalEmojis(guildEmojis)
        if not importing:
            self._add_default_role_groups()
            self._add_default_roles()

    @property
    def additional_role_count(self) -> int:
        return len(self.roleGroups["Additional"])

    @property
    def color(self) -> int:
        if self.dlc and self.sideop:
            return EMBED_COLOR['DLC_SIDEOP']
        if self.dlc:
            return EMBED_COLOR['DLC']
        if self.sideop:
            return EMBED_COLOR['SIDEOP']
        return EMBED_COLOR['DEFAULT']

    @property
    def title(self) -> str:
        if self._title:
            # It an explicit title is set, return that
            return self._title
        # Otherwise, use dynamic title
        if self.dlc and self.sideop:
            return f"{self.dlc} {SIDEOP_TITLE}"
        if self.dlc:
            return f"{self.dlc} {TITLE}"
        if self.sideop:
            return SIDEOP_TITLE
        return TITLE

    @title.setter
    def title(self, title):
        self._title = title

    def changeSize(self, new_size):
        # pylint: disable=too-many-statements
        if new_size == self.platoon_size:
            return None

        if self.sideop:
            return None

        if new_size not in cfg.PLATOON_SIZES:
            raise ValueError(f"Unsupported new platoon size: {new_size}")

        def _moveRole(roleName, sourceGroup: RoleGroup, targetGroupName=None):
            print("sourcegroup", type(sourceGroup), sourceGroup.name)
            msg = ""
            role = sourceGroup[roleName]
            print(f"moving role {roleName} from {sourceGroup.name} to "
                  f"{targetGroupName}")
            if targetGroupName is None:
                if role.userID is not None:
                    msg = (f"Warning: removing an active role {role} "
                           f"from {sourceGroup.name}, {self}")
                    print("removing active role")
                sourceGroup.removeRole(roleName)
            else:
                if targetGroupName not in self.roleGroups:
                    print("creating target group")
                    self.roleGroups[targetGroupName] = \
                        RoleGroup(targetGroupName)
                self.roleGroups[targetGroupName][roleName] = role
                self.roleGroups[sourceGroup.name].removeRole(roleName)
            if not self.roleGroups[sourceGroup.name]:
                print("deleting target group")
                del self.roleGroups[sourceGroup.name]
            return msg

        def _getTargetGroup(new_groups: List[str]) -> str:
            for new_group in new_groups:
                if new_group not in self.roleGroups:
                    new_groups.remove(new_group)
                    return new_group
            raise RoleGroupNotFound(f"Could not find a group for {new_groups}")

        warnings = ""
        if self.platoon_size == "2PLT":
            if new_size == "1PLT":
                new_groups = ["Charlie", "Delta"]

                sourceGroup = self.roleGroups["Battalion"]
                msg = _moveRole("ZEUS", sourceGroup, "Company")
                if msg != "":
                    print(msg)
                    warnings += msg + '\n'

                sourceGroup = self.roleGroups["Company"]
                for roleName in ["FAC", "RTO"]:
                    msg = _moveRole(roleName, sourceGroup,
                                    "1st Platoon")
                    if msg != "":
                        print(msg)
                        warnings += msg + '\n'
                sourceGroup = self.roleGroups["Company"]
                msg = _moveRole("CO", sourceGroup, None)
                if msg != "":
                    print(msg)
                    warnings += msg + '\n'

                sourceGroup = self.roleGroups["2nd Platoon"]
                msg = _moveRole("2PLT", self.roleGroups["2nd Platoon"], None)
                if msg != "":
                    print(msg)
                    warnings += msg + '\n'

                targetGroup = _getTargetGroup(new_groups)
                sourceGroupName = "Echo"
                sourceGroup = self.roleGroups[sourceGroupName]
                for roleName in ["ESL", "E1"]:
                    msg = _moveRole(roleName, sourceGroup, targetGroup)
                    if msg != "":
                        print(msg)
                        warnings += msg + '\n'

                targetGroup = _getTargetGroup(new_groups)
                sourceGroupName = "Foxtrot"
                sourceGroup = self.roleGroups[sourceGroupName]
                signupFound = False
                for roleName in ["FSL", "F1"]:
                    if sourceGroup[roleName].userID is not None:
                        signupFound = True
                        break
                if signupFound:
                    for roleName in ["FSL", "F1"]:
                        msg = _moveRole(roleName, sourceGroup, targetGroup)
                        print(msg)
                        warnings += msg + '\n'
                else:
                    del self.roleGroups[sourceGroupName]

                del self.roleGroups["Dummy"]

                newGroups = {}
                for key, value in self.roleGroups.items():
                    newGroups[key] = value
                    if value.name == "1st Platoon":
                        newGroups["Dummy"] = RoleGroup("Dummy")

                self.roleGroups = newGroups

                self.platoon_size = "1PLT"

            else:
                raise ValueError("Unsupported platoon size conversion: "
                                 f"{self.platoon_size} -> {new_size}")
        elif self.platoon_size == "1PLT":
            if new_size == "2PLT":
                # TODO: implement 1PLT -> 2PLT conversion
                raise NotImplementedError("Conversion from 1PLT to 2PLT "
                                          "not implemented")
            raise ValueError("Unsupported platoon size conversion: "
                             f"{self.platoon_size} -> {new_size}")
        else:
            raise ValueError("Unsupported current platoon size: "
                             f"{self.platoon_size}")
        return warnings

    def reorder(self):
        if self.sideop:
            return None

        newGroups = {}
        warnings = ""
        for groupName in cfg.DEFAULT_GROUPS[self.platoon_size] + \
                ["Additional"]:
            try:
                group = self.roleGroups[groupName]
            except KeyError:
                group = RoleGroup("Dummy")
                msg = f"Could not find group {groupName}"
                print(msg)
                warnings += msg + '\n'
            newGroups[groupName] = group
        self.roleGroups = newGroups
        return warnings

    # Return an embed for the event
    def createEmbed(self) -> Embed:
        date_tz = self.date.replace(tzinfo=cfg.TIME_ZONE)
        date = date_tz.strftime(f"%a %Y-%m-%d - %H:%M {date_tz.tzname()}")
        title = f"{self.title} ({date})"
        timestamp = int(date_tz.astimezone(datetime.timezone.utc).timestamp())
        local_time = f"<t:{timestamp}>"
        relative_time = f"<t:{timestamp}:R>"
        server_port = (f"\nServer port: **{self.port}**"
                       if self.port != cfg.PORT_DEFAULT else "")
        dlc_note = (f"\n\nThe **{self.dlc} DLC** is required to "
                    "join this event"
                    if self.dlc else "")
        event_description = (f"\n\n{self.description}"
                             if self.description else "")
        if self.mods:
            if '\n' in self.mods:
                mods = f"\n\nMods:\n{self.mods}\n"
            else:
                mods = f"\n\nMods: {self.mods}\n"
        else:
            mods = ""
        description = (f"Local time: {local_time} ({relative_time})\n"
                       f"Terrain: {self.terrain} - Faction: {self.faction}"
                       f"{server_port}"
                       f"{dlc_note}"
                       f"{event_description}"
                       f"{mods}")
        eventEmbed = Embed(title=title, description=description,
                           colour=self.color)

        # Add field to embed for every rolegroup
        for group in self.roleGroups.values():
            if len(group.roles) > 0:
                eventEmbed.add_field(name=group.name, value=str(group),
                                     inline=group.isInline)
            elif group.name == "Dummy":
                eventEmbed.add_field(name="\N{ZERO WIDTH SPACE}",
                                     value="\N{ZERO WIDTH SPACE}",
                                     inline=group.isInline)

        if self.sideop or cfg.ALWAYS_DISPLAY_ATTENDANCE:
            attendees = f"Attendees: {len(self.attendees)}\n\n"
        else:
            attendees = ""
        eventEmbed.set_footer(text=f"{attendees}Event ID: {str(self.id)}")

        return eventEmbed

    # Add default role groups
    def _add_default_role_groups(self):
        for group in cfg.DEFAULT_GROUPS[self.platoon_size]:
            self.roleGroups[group] = RoleGroup(group)
        self.roleGroups["Additional"] = AdditionalRoleGroup()

    # Add default roles
    def _add_default_roles(self):
        for name, groupName in cfg.DEFAULT_ROLES[self.platoon_size].items():
            # Only add role if the group exists
            if groupName in self.roleGroups:
                emoji = self.normalEmojis[name]
                newRole = Role(name, emoji, False)
                self.roleGroups[groupName].addRole(newRole)

    # Add an additional role to the event
    def addAdditionalRole(self, name: str) -> str:

        # check if this role already exists
        for roleGroup in self.roleGroups.values():
            role: Role
            for role in roleGroup.roles:
                if role.name == name:
                    raise RoleError(f"Role with name {name} already exists, "
                                    "not adding new role")

        # Find next emoji for additional role
        if self.countReactions() >= MAX_REACTIONS:
            raise RoleError(f"Too many roles, not adding role {name}")
        emoji = cfg.ADDITIONAL_ROLE_EMOJIS[self.additional_role_count]

        # Create role
        newRole = Role(name, emoji, show_name=True)

        # Add role to additional roles
        self.roleGroups["Additional"].addRole(newRole)

        return emoji

    def _check_additional(self, role: Role):
        """Raises a RoleError if the supplied role is not an additional role"""
        if role not in self.roleGroups["Additional"].roles:
            raise RoleError(f"Role {role.name} is not an additional role")

    def renameAdditionalRole(self, role: Role, new_name: str):
        """Rename an additional role in the event."""
        self._check_additional(role)
        role.name = new_name

    def removeAdditionalRole(self, role: Union[str, Role]):
        """Remove an additional role from the event."""
        # Remove role from additional roles
        if isinstance(role, Role):
            self._check_additional(role)
        self.roleGroups["Additional"].removeRole(role)

    def removeRoleGroup(self, groupName: str) -> bool:
        """
        Remove a role group.

        Returns false if the group cannot be found.
        """
        if groupName not in self.roleGroups:
            return False
        self.roleGroups.pop(groupName, None)
        return True

    @property
    def time(self):
        return datetime.time(hour=self.date.hour, minute=self.date.minute)

    @time.setter
    def time(self, time: Union[datetime.time, datetime.datetime]):
        self.date = self.date.replace(hour=time.hour, minute=time.minute)

    @property
    def terrain(self) -> str:
        return self._terrain

    @terrain.setter
    def terrain(self, terrain):
        if terrain in cfg.DLC_TERRAINS:
            self.dlc = cfg.DLC_TERRAINS[terrain]
        else:
            self.dlc = None
        self._terrain = terrain

    # Get emojis for normal roles
    def _getNormalEmojis(self, guildEmojis: Tuple[Emoji, ...]) \
            -> Dict[str, Emoji]:
        normalEmojis = {}

        for emoji in guildEmojis:
            if emoji.name in cfg.DEFAULT_ROLES[self.platoon_size]:
                normalEmojis[emoji.name] = emoji

        return normalEmojis

    def getReactions(self) -> List[Union[str, Emoji]]:
        """Return reactions of all roles and extra reactions"""
        reactions = []

        for roleGroup in self.roleGroups.values():
            role: Role
            for role in roleGroup.roles:
                emoji = role.emoji
                # Skip the ZEUS reaction. Zeuses can only be signed up using
                # the signup command
                if not (isinstance(emoji, Emoji)
                        and emoji.name == cfg.EMOJI_ZEUS):
                    reactions.append(role.emoji)

        if self.sideop or cfg.ALWAYS_DISPLAY_ATTENDANCE:
            if cfg.ATTENDANCE_EMOJI:
                reactions.append(cfg.ATTENDANCE_EMOJI)

        return reactions

    def countReactions(self) -> int:
        """Count how many reactions a message should have."""
        return len(self.getReactions())

    def getReactionsOfGroup(self, groupName: str) -> List[Union[str, Emoji]]:
        """Find reactions of a given role group."""
        reactions = []

        if groupName in self.roleGroups:
            for role in self.roleGroups[groupName].roles:
                reactions.append(role.emoji)

        return reactions

    def findRoleWithEmoji(self, emoji) -> Role:
        """Find a role with given emoji."""
        for roleGroup in self.roleGroups.values():
            for role in roleGroup.roles:
                if role.emoji == emoji:
                    return role
        raise RoleNotFound(f"No role found with emoji {emoji}")

    def findRoleWithName(self, roleName: str) -> Role:
        """Find a role with given name.

        Raises a RoleNotFound if the role cannot be found."""
        roleName = roleName.lower()
        for roleGroup in self.roleGroups.values():
            role: Role
            for role in roleGroup.roles:
                if role.name.lower() == roleName:
                    return role
        raise RoleNotFound(f"No role found with name {roleName}")

    def getRoleGroup(self, groupName: str) -> RoleGroup:
        try:
            return self.roleGroups[groupName]
        except KeyError as e:
            raise RoleGroupNotFound("No role group found with name "
                                    f"{groupName}") from e

    def hasRoleGroup(self, groupName: str) -> bool:
        """Check if a role group with given name exists in the event."""
        return groupName in self.roleGroups

    def get_additional_role(self, role_name: str) -> Role:
        return self.roleGroups["Additional"][role_name]

    def signup(self, roleToSet: Role, user: discord.abc.User, replace=False) \
            -> Tuple[Optional[Role], User]:
        """Add username to role.

        Raises an error if the role is taken, unless replace is set to True.

        Returns a tuple containing the role current user was removed from (if
        any) and the signed-up user that this command replaced. If no user was
        replaced, the returned User has ID = None, name = ''
        """
        for roleGroup in self.roleGroups.values():
            for role in roleGroup.roles:
                if role == roleToSet:
                    if role.userID and not replace:
                        raise RoleTaken(f"Can't sign up {user.display_name}, "
                                        f"role {roleToSet.name} is already "
                                        "taken")
                    old_user = User(role.userID, role.userName)
                    old_role = self.undoSignup(user)
                    role.userID = user.id
                    role.userName = user.display_name
                    return old_role, old_user
        # Probably shouldn't ever reach this
        raise RoleNotFound(f"Could not find role: {roleToSet}")

    def undoSignup(self, user) -> Optional[Role]:
        """Remove username from any signups.

        Returns Role if user was signed up, otherwise None."""
        for roleGroup in self.roleGroups.values():
            for role in roleGroup.roles:
                if role.userID == user.id:
                    role.userID = None
                    role.userName = ""
                    return role
        return None

    def findSignupRole(self, userID) -> Optional[Role]:
        """Check if given user is already signed up."""
        for roleGroup in self.roleGroups.values():
            for role in roleGroup.roles:
                if role.userID == int(userID):
                    return role
        # TODO: raise RoleNotFound instead of returning None?
        return None

    def has_attendee(self, user: discord.abc.User) -> bool:
        """Check if the given user has been marked as attending."""
        return user in self.attendees

    def add_attendee(self, user: discord.abc.User) -> None:
        """Add user to the attendance list"""
        if not self.has_attendee(user):
            self.attendees.append(
                User(id=user.id, display_name=user.display_name))

    def remove_attendee(self, user: discord.abc.User) -> None:
        """Remove user from the attendance list"""
        if self.has_attendee(user):
            self.attendees.remove(user)

    def __str__(self):
        return f"{self.title} (ID {self.id}) at {self.date}"

    def __repr__(self):
        return f"<Event title='{self.title}' id={self.id} date='{self.date}'>"

    def toJson(self, brief_output=False) -> Dict[str, Any]:
        roleGroupsData = {}
        for groupName, roleGroup in self.roleGroups.items():
            roleGroupsData[groupName] = roleGroup.toJson(brief_output)

        attendees_data = {}
        for user in self.attendees:
            attendees_data[user.id] = user.display_name

        data: Dict[str, Any] = {}
        data["title"] = self._title
        data["date"] = self.date.strftime("%Y-%m-%d")
        data["description"] = self.description
        data["time"] = self.date.strftime("%H:%M")
        data["terrain"] = self.terrain
        data["faction"] = self.faction
        data["port"] = self.port
        data["mods"] = self.mods
        if not brief_output:
            data["messageID"] = self.messageID
            data["platoon_size"] = self.platoon_size
            data["sideop"] = self.sideop
            data["attendees"] = attendees_data
        data["roleGroups"] = roleGroupsData
        return data

    def fromJson(self, eventID, data: dict, emojis, manual_load=False):
        self.id = int(eventID)
        self.title = data.get("title", None)
        self.time = datetime.datetime.strptime(data.get("time", "00:00"),
                                               "%H:%M")
        self.terrain = data.get("terrain", TERRAIN)
        self.faction = str(data.get("faction", FACTION))
        self.port = int(data.get("port", cfg.PORT_DEFAULT))
        self.description = str(data.get("description", DESCRIPTION))
        self.mods = str(data.get("mods", MODS))
        if not manual_load:
            self.messageID = int(data.get("messageID", 0))
            self.platoon_size = str(data.get("platoon_size", PLATOON_SIZE))
            self.sideop = bool(data.get("sideop", False))
            attendees_data = data.get("attendees", {})
            for userID, name in attendees_data.items():
                self.attendees.append(User(int(userID), name))

        # TODO: Handle missing roleGroups
        groups: List[str] = []
        for groupName, roleGroupData in data["roleGroups"].items():
            if not manual_load:
                # Only create new role groups if we're not loading data
                # manually from the command channel
                if groupName != "Additional":
                    roleGroup = RoleGroup(groupName)
                else:
                    roleGroup = AdditionalRoleGroup()
                self.roleGroups[groupName] = roleGroup
            else:
                roleGroup = self.roleGroups[groupName]
                groups.append(groupName)
            roleGroup.fromJson(roleGroupData, emojis, manual_load)
        if manual_load:
            # Remove role groups that were not present in imported data
            for group in list(self.roleGroups.keys()):
                if group not in groups:
                    del self.roleGroups[group]
