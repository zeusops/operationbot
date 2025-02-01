import datetime
import hashlib
import logging
from typing import Any, Union

import discord
from discord import Embed, Emoji

from operationbot import config as cfg
from operationbot.additional_role_group import AdditionalRoleGroup
from operationbot.config import EMBED_COLOR, OVERHAUL_MODS
from operationbot.errors import RoleError, RoleGroupNotFound, RoleNotFound, RoleTaken
from operationbot.role import Role
from operationbot.roleGroup import RoleGroup
from operationbot.secret import PLATOON_SIZE

TITLE = "Operation"
REFORGER = "Reforger"
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
    def __init__(self, id: int | None = None, display_name: str | None = None):
        self.id = id
        self.display_name = display_name

    def __eq__(self, other: Union["User", discord.abc.User]):  # type: ignore
        # This makes it so that User objects can be compared to
        # discord.abc.User by doing `user == discord.abc.User`. The comparison
        # will not work in the other direction because discord.abc.User checks
        # for the object type.
        return self.id == other.id


class Event:
    def __init__(
        self,
        date: datetime.datetime,
        guildEmojis: tuple[Emoji, ...],
        eventID=0,
        importing=False,
        sideop=False,
        platoon_size=None,
        reforger=False,
    ):
        self._title: str | None = None
        self.date = date
        self.terrain = TERRAIN
        self.faction = FACTION
        self._description = ""
        self.port = cfg.PORT_DEFAULT
        self._mods = ""
        self.roleGroups: dict[str, RoleGroup] = {}
        self.messageID = 0
        self.id = eventID
        self.sideop = sideop
        self.reforger = reforger
        self.attendees: list[User | discord.abc.User] = []
        self._dlc: str = ""
        self.overhaul = ""
        self.embed_hash = ""
        self.cancelled = False

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
        if self.cancelled:
            return EMBED_COLOR["CANCELLED"]
        if self.overhaul:
            return EMBED_COLOR["OVERHAUL"]
        if self.reforger and self.dlc and self.sideop:
            return EMBED_COLOR["REFORGER_DLC_SIDEOP"]
        if self.reforger and self.dlc:
            return EMBED_COLOR["REFORGER_DLC"]
        if self.reforger and self.sideop:
            return EMBED_COLOR["REFORGER_SIDEOP"]
        if self.dlc and self.sideop:
            return EMBED_COLOR["DLC_SIDEOP"]
        if self.dlc:
            return EMBED_COLOR["DLC"]
        if self.sideop:
            return EMBED_COLOR["SIDEOP"]
        if self.reforger:
            return EMBED_COLOR["REFORGER"]
        return EMBED_COLOR["DEFAULT"]

    @property
    def title(self) -> str:
        if self._title:
            # It an explicit title is set, return that
            return self._title
        # Otherwise, use dynamic title
        if self.cancelled:
            return f"Cancelled {TITLE}"
        if self.overhaul:
            return f"{self.overhaul} Overhaul {TITLE}"
        if self.reforger and self.dlc and self.sideop:
            return f"{self.dlc} {REFORGER} {SIDEOP_TITLE}"
        if self.reforger and self.dlc:
            return f"{self.dlc} {REFORGER}"
        if self.reforger and self.sideop:
            return f"{REFORGER} {SIDEOP_TITLE}"
        if self.dlc and self.sideop:
            return f"{self.dlc} {SIDEOP_TITLE}"
        if self.dlc:
            return f"{self.dlc} {TITLE}"
        if self.sideop:
            return SIDEOP_TITLE
        if self.reforger:
            return f"{REFORGER} {TITLE}"
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
            print(
                f"moving role {roleName} from {sourceGroup.name} to "
                f"{targetGroupName}"
            )
            if targetGroupName is None:
                if role.userID is not None:
                    msg = (
                        f"Warning: removing an active role {role} "
                        f"from {sourceGroup.name}, {self}"
                    )
                    print("removing active role")
                sourceGroup.removeRole(roleName)
            else:
                if targetGroupName not in self.roleGroups:
                    print("creating target group")
                    self.roleGroups[targetGroupName] = RoleGroup(targetGroupName)
                self.roleGroups[targetGroupName][roleName] = role
                self.roleGroups[sourceGroup.name].removeRole(roleName)
            if not self.roleGroups[sourceGroup.name]:
                print("deleting target group")
                del self.roleGroups[sourceGroup.name]
            return msg

        def _getTargetGroup(new_groups: list[str]) -> str:
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
                    warnings += msg + "\n"

                sourceGroup = self.roleGroups["Company"]
                for roleName in ["FAC", "RTO"]:
                    msg = _moveRole(roleName, sourceGroup, "1st Platoon")
                    if msg != "":
                        print(msg)
                        warnings += msg + "\n"
                sourceGroup = self.roleGroups["Company"]
                msg = _moveRole("CO", sourceGroup, None)
                if msg != "":
                    print(msg)
                    warnings += msg + "\n"

                sourceGroup = self.roleGroups["2nd Platoon"]
                msg = _moveRole("2PLT", self.roleGroups["2nd Platoon"], None)
                if msg != "":
                    print(msg)
                    warnings += msg + "\n"

                targetGroup = _getTargetGroup(new_groups)
                sourceGroupName = "Echo"
                sourceGroup = self.roleGroups[sourceGroupName]
                for roleName in ["ESL", "E1"]:
                    msg = _moveRole(roleName, sourceGroup, targetGroup)
                    if msg != "":
                        print(msg)
                        warnings += msg + "\n"

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
                        warnings += msg + "\n"
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
                raise ValueError(
                    "Unsupported platoon size conversion: "
                    f"{self.platoon_size} -> {new_size}"
                )
        elif self.platoon_size == "1PLT":
            if new_size == "2PLT":
                # TODO: implement 1PLT -> 2PLT conversion
                raise NotImplementedError(
                    "Conversion from 1PLT to 2PLT not implemented"
                )
            raise ValueError(
                "Unsupported platoon size conversion: "
                f"{self.platoon_size} -> {new_size}"
            )
        else:
            raise ValueError(f"Unsupported current platoon size: {self.platoon_size}")
        return warnings

    def reorder(self):
        if self.sideop:
            return None

        newGroups = {}
        warnings = ""
        for groupName in cfg.DEFAULT_GROUPS[self.platoon_size] + ["Additional"]:
            try:
                group = self.roleGroups[groupName]
            except KeyError:
                group = RoleGroup("Dummy")
                msg = f"Could not find group {groupName}"
                print(msg)
                warnings += msg + "\n"
            newGroups[groupName] = group
        self.roleGroups = newGroups
        return warnings

    # Return an embed for the event
    def createEmbed(self, cache=True) -> Embed | None:
        logging.info(f"Creating embed for {self}")
        date_tz = self.date.replace(tzinfo=cfg.TIME_ZONE)
        date = date_tz.strftime(f"%a %Y-%m-%d - %H:%M {date_tz.tzname()}")
        title = f"{self.title} ({date})"
        timestamp = int(date_tz.astimezone(datetime.timezone.utc).timestamp())
        local_time = f"<t:{timestamp}>"
        relative_time = f"<t:{timestamp}:R>"
        server_port = (
            f"\nServer port: **{self.port}**" if self.port != cfg.PORT_DEFAULT else ""
        )
        reforger_note = (
            "\n\n**Arma Reforger** is required to join this event"
            if self.reforger
            else ""
        )
        dlc_note = (
            f"\n\nThe **{self.dlc} DLC** is required to join this event"
            if self.dlc
            else ""
        )
        event_description = f"\n\n{self.description}" if self.description else ""
        if self.mods:
            if "\n" in self.mods:
                mods = f"\n\nMods:\n{self.mods}\n"
            else:
                mods = f"\n\nMods: {self.mods}\n"
        else:
            mods = ""
        description = (
            f"Local time: {local_time} ({relative_time})\n"
            f"Terrain: {self.terrain} - Faction: {self.faction}"
            f"{server_port}"
            f"{reforger_note}"
            f"{dlc_note}"
            f"{event_description}"
            f"{mods}"
        )
        eventEmbed = Embed(title=title, description=description, colour=self.color)
        hash_string = f"{title}\n{description}\n{self.color}\n"

        # Add field to embed for every rolegroup
        for group in self.roleGroups.values():
            if len(group.roles) > 0:
                eventEmbed.add_field(
                    name=group.name, value=str(group), inline=group.isInline
                )
                hash_string += (
                    f"{hash_string}{group.name} {str(group)} " f"{group.isInline}\n"
                )
            elif group.name.startswith("Dummy"):
                eventEmbed.add_field(
                    name="\N{ZERO WIDTH SPACE}",
                    value="\N{ZERO WIDTH SPACE}",
                    inline=group.isInline,
                )
                hash_string += f"{hash_string}{group.name}\n"

        if self.sideop or cfg.ALWAYS_DISPLAY_ATTENDANCE:
            attendees = f"Attendees: {len(self.attendees)}\n\n"
        else:
            attendees = ""
        footer_text = f"{attendees}Event ID: {str(self.id)}"
        eventEmbed.set_footer(text=footer_text)
        hash_string += f"{hash_string}{footer_text}\n"
        embed_hash = hashlib.sha256(hash_string.encode("utf-8")).hexdigest()
        if cache:
            if embed_hash == self.embed_hash:
                logging.info("Embed is unchanged, not updating")
                return None
            logging.info("Cached embed is changed, updating")
            self.embed_hash = embed_hash
        else:
            logging.info("Ignoring cache")
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
                    raise RoleError(
                        f"Role with name {name} already exists, not adding new role"
                    )

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

    def removeAdditionalRole(self, role: str | Role):
        """Remove an additional role from the event."""
        # Remove role from additional roles
        if isinstance(role, Role):
            self._check_additional(role)
        self.roleGroups["Additional"].removeRole(role)

    def removeRoleGroup(self, groupName: str) -> bool:
        """Remove a role group.

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
    def time(self, time: datetime.time | datetime.datetime):
        self.date = self.date.replace(hour=time.hour, minute=time.minute)

    @property
    def dlc(self) -> str:
        if self._dlc:
            return self._dlc
        if self.terrain in cfg.DLC_TERRAINS:
            return cfg.DLC_TERRAINS[self.terrain]
        return ""

    @dlc.setter
    def dlc(self, dlc):
        self._dlc = dlc

    @property
    def description(self) -> str:
        if self._description:
            return self._description
        return DESCRIPTION

    @description.setter
    def description(self, description):
        self._description = description

    @property
    def mods(self) -> str:
        if self._mods:
            return self._mods
        if self.overhaul:
            return OVERHAUL_MODS
        return MODS

    @mods.setter
    def mods(self, mods):
        self._mods = mods

    # Get emojis for normal roles
    def _getNormalEmojis(self, guildEmojis: tuple[Emoji, ...]) -> dict[str, Emoji]:
        normalEmojis = {}

        for emoji in guildEmojis:
            if emoji.name in cfg.DEFAULT_ROLES[self.platoon_size]:
                normalEmojis[emoji.name] = emoji

        return normalEmojis

    def getReactions(self) -> list[str | Emoji]:
        """Return reactions of all roles and extra reactions"""
        if self.cancelled:
            return []

        reactions = []

        for roleGroup in self.roleGroups.values():
            role: Role
            for role in roleGroup.roles:
                emoji = role.emoji
                # Skip the ZEUS reaction. Zeuses can only be signed up using
                # the signup command
                if not (isinstance(emoji, Emoji) and emoji.name == cfg.EMOJI_ZEUS):
                    reactions.append(role.emoji)

        if self.sideop or cfg.ALWAYS_DISPLAY_ATTENDANCE:
            if cfg.ATTENDANCE_EMOJI:
                reactions.append(cfg.ATTENDANCE_EMOJI)

        return reactions

    def countReactions(self) -> int:
        """Count how many reactions a message should have."""
        return len(self.getReactions())

    def getReactionsOfGroup(self, groupName: str) -> list[str | Emoji]:
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

        Raises a RoleNotFound if the role cannot be found.
        """
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
            raise RoleGroupNotFound(f"No role group found with name {groupName}") from e

    def hasRoleGroup(self, groupName: str) -> bool:
        """Check if a role group with given name exists in the event."""
        return groupName in self.roleGroups

    def get_additional_role(self, role_name: str) -> Role:
        return self.roleGroups["Additional"][role_name]

    def signup(
        self, roleToSet: Role, user: discord.abc.User, replace=False
    ) -> tuple[Role | None, User]:
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
                        raise RoleTaken(
                            f"Can't sign up {user.display_name}, "
                            f"role {roleToSet.name} is already "
                            "taken"
                        )
                    old_user = User(role.userID, role.userName)
                    old_role = self.undoSignup(user)
                    role.userID = user.id
                    role.userName = user.display_name
                    self.cancelled = False
                    return old_role, old_user
        # Probably shouldn't ever reach this
        raise RoleNotFound(f"Could not find role: {roleToSet}")

    def undoSignup(self, user) -> Role | None:
        """Remove username from any signups.

        Returns Role if user was signed up, otherwise None.
        """
        for roleGroup in self.roleGroups.values():
            for role in roleGroup.roles:
                if role.userID == user.id:
                    role.userID = None
                    role.userName = ""
                    return role
        return None

    def findSignupRole(self, userID) -> Role | None:
        """Check if given user is already signed up."""
        for roleGroup in self.roleGroups.values():
            for role in roleGroup.roles:
                if role.userID == int(userID):
                    return role
        # TODO: raise RoleNotFound instead of returning None?
        return None

    def is_empty(self) -> bool:
        role = self.findRoleWithName("ZEUS")
        if not role:
            return False
        return role.userID is None

    def has_attendee(self, user: discord.abc.User) -> bool:
        """Check if the given user has been marked as attending."""
        return user in self.attendees

    def add_attendee(self, user: discord.abc.User) -> None:
        """Add user to the attendance list"""
        if not self.has_attendee(user):
            self.attendees.append(User(id=user.id, display_name=user.display_name))

    def remove_attendee(self, user: discord.abc.User) -> None:
        """Remove user from the attendance list"""
        if self.has_attendee(user):
            self.attendees.remove(user)

    def __str__(self):
        return f"{self.title} (ID {self.id}) at {self.date}"

    def __repr__(self):
        return f"<Event title='{self.title}' id={self.id} date='{self.date}'>"

    def toJson(self, brief_output=False) -> dict[str, Any]:
        roleGroupsData = {}
        for groupName, roleGroup in self.roleGroups.items():
            roleGroupsData[groupName] = roleGroup.toJson(brief_output)

        attendees_data = {}
        for user in self.attendees:
            attendees_data[user.id] = user.display_name

        data: dict[str, Any] = {}
        data["title"] = self._title
        data["date"] = self.date.strftime("%Y-%m-%d")
        data["description"] = self._description
        data["time"] = self.date.strftime("%H:%M")
        data["terrain"] = self.terrain
        data["faction"] = self.faction
        data["port"] = self.port
        data["mods"] = self._mods
        data["dlc"] = self._dlc
        data["overhaul"] = self.overhaul
        if not brief_output:
            data["messageID"] = self.messageID
            data["platoon_size"] = self.platoon_size
            data["sideop"] = self.sideop
            data["reforger"] = self.reforger
            data["attendees"] = attendees_data
            data["embed_hash"] = self.embed_hash
            data["cancelled"] = self.cancelled
        data["roleGroups"] = roleGroupsData
        return data

    def fromJson(self, eventID, data: dict, emojis, manual_load=False):
        self.id = int(eventID)
        self.title = data.get("title", None)
        self.time = datetime.datetime.strptime(data.get("time", "00:00"), "%H:%M")
        self.terrain = data.get("terrain", TERRAIN)
        self.faction = str(data.get("faction", FACTION))
        self.port = int(data.get("port", cfg.PORT_DEFAULT))
        self._description = str(data.get("description", ""))
        self._mods = str(data.get("mods", ""))
        self.dlc = data.get("dlc", "")
        self.overhaul = data.get("overhaul", "")
        if not manual_load:
            self.messageID = int(data.get("messageID", 0))
            self.platoon_size = str(data.get("platoon_size", PLATOON_SIZE))
            self.sideop = bool(data.get("sideop", False))
            self.reforger = bool(data.get("reforger", False))
            self.embed_hash = data.get("embed_hash", "")
            self.cancelled = data.get("cancelled", False)
            attendees_data = data.get("attendees", {})
            for userID, name in attendees_data.items():
                self.attendees.append(User(int(userID), name))

        # TODO: Handle missing roleGroups
        groups: list[str] = []
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
