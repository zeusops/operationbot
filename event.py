from datetime import datetime
from typing import Dict, List, Optional, Tuple

from discord import Embed, Emoji

import config as cfg
from secret import PLATOON_SIZE
from role import Role
from roleGroup import RoleGroup

TITLE = "Operation"
SIDEOP_TITLE = "Side Operation"
TERRAIN = "unknown"
FACTION = "unknown"
DESCRIPTION = ""
COLOR = 0xFF4500
SIDEOP_COLOR = 0x0045FF
WW2_SIDEOP_COLOR = 0x808080
# Discord API limitation
MAX_REACTIONS = 20


class RoleError(Exception):
    pass


class User:
    def __init__(self, id: id = None, display_name: str = None):
        self.id = id
        self.display_name = display_name


class Event:

    def __init__(self, date: datetime, guildEmojis: Tuple[Emoji], eventID=0,
                 importing=False, sideop=False, platoon_size=None):
        self.title = TITLE if not sideop else SIDEOP_TITLE
        self.date = date
        self.terrain = TERRAIN
        self.faction = FACTION
        self.description = DESCRIPTION
        self.color = COLOR if not sideop else SIDEOP_COLOR
        self.roleGroups: Dict[str, RoleGroup] = {}
        self.additionalRoleCount = 0
        self.messageID = 0
        self.id = eventID
        self.sideop = sideop
        if platoon_size is None:
            if sideop:
                self.platoon_size = "sideop"
            else:
                self.platoon_size = PLATOON_SIZE
        elif platoon_size in cfg.PLATOON_SIZES:
            self.platoon_size = platoon_size
        else:
            raise ValueError("Unsupported platoon size: {}"
                             .format(platoon_size))

        if self.platoon_size.startswith("WW2"):
            self.title = "WW2 " + self.title
            if sideop:
                self.color = WW2_SIDEOP_COLOR
            else:
                # no WW2 main operations are happening right now
                pass

        self.normalEmojis = self._getNormalEmojis(guildEmojis)
        if not importing:
            self.addDefaultRoleGroups()
            self.addDefaultRoles()

    def changeSize(self, new_size):
        if new_size == self.platoon_size:
            return None

        if self.sideop:
            return None

        if new_size not in cfg.PLATOON_SIZES:
            raise ValueError("Unsupported new platoon size: {}"
                             .format(new_size))

        def _moveRole(roleName, sourceGroup: RoleGroup, targetGroupName=None):
            print("sourcegroup", type(sourceGroup), sourceGroup.name)
            msg = ""
            role = sourceGroup[roleName]
            print("moving role {} from {} to {}".format(roleName, sourceGroup.name, targetGroupName))
            if targetGroupName is None:
                if role.userID is not None:
                    msg = "Warning: removing an active role {} from {}, {}" \
                          .format(role, sourceGroup.name, self)
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

        def _getTargetGroup(new_groups):
            for new_group in new_groups:
                if new_group not in self.roleGroups:
                    new_groups.remove(new_group)
                    return new_group

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
                raise ValueError("Unsupported platoon size conversion: {} -> {}"
                                 .format(self.platoon_size, new_size))
        elif self.platoon_size == "1PLT":
            if new_size == "2PLT":
                # TODO: implement 1PLT -> 2PLT conversion
                raise NotImplementedError("Conversion from 1PLT to 2PLT " \
                                          "not implemented")
            raise ValueError("Unsupported platoon size conversion: {} -> {}"
                             .format(self.platoon_size, new_size))
        else:
            raise ValueError("Unsupported current platoon size: {}"
                             .format(self.platoon_size))
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
                msg = "Could not find group {}".format(groupName)
                print(msg)
                warnings += msg + '\n'
            newGroups[groupName] = group
        self.roleGroups = newGroups
        return warnings


    # Return an embed for the event
    def createEmbed(self) -> Embed:
        title = "{} ({})".format(
            self.title, self.date.strftime("%a %Y-%m-%d - %H:%M CET"))
        description = "Terrain: {} - Faction: {}\n\n{}".format(
            self.terrain, self.faction, self.description)
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

        return eventEmbed

    # Add default role groups
    def addDefaultRoleGroups(self):
        for group in cfg.DEFAULT_GROUPS[self.platoon_size]:
            self.roleGroups[group] = RoleGroup(group)
        self.roleGroups["Additional"] = RoleGroup("Additional",
                                                  isInline=False)

    # Add default roles
    def addDefaultRoles(self):
        for name, groupName in cfg.DEFAULT_ROLES[self.platoon_size].items():
            # Only add role if the group exists
            if groupName in self.roleGroups.keys():
                emoji = self.normalEmojis[name]
                newRole = Role(name, emoji, False)
                self.roleGroups[groupName].addRole(newRole)

    # Add an additional role to the event
    def addAdditionalRole(self, name: str) -> str:
        # Find next emoji for additional role

        if self.countReactions() >= MAX_REACTIONS:
            raise RoleError("Too many roles.")
        emoji = cfg.ADDITIONAL_ROLE_EMOJIS[self.additionalRoleCount]

        # Create role
        newRole = Role(name, emoji, True)

        # Add role to additional roles
        self.roleGroups["Additional"].addRole(newRole)
        self.additionalRoleCount += 1

        return emoji

    def removeAdditionalRole(self, role: str):
        """Remove an additional role from the event."""
        # Remove role from additional roles
        self.roleGroups["Additional"].removeRole(role)

        # Reorder the emotes of all the additional roles
        self.additionalRoleCount = 0
        for roleInstance in self.roleGroups["Additional"].roles:
            emoji = cfg.ADDITIONAL_ROLE_EMOJIS[self.additionalRoleCount]
            roleInstance.emoji = emoji
            self.additionalRoleCount += 1

    def removeRoleGroup(self, groupName: str) -> bool:
        """
        Remove a role group.

        Returns false if the group cannot be found.
        """
        if groupName not in self.roleGroups:
            return False
        self.roleGroups.pop(groupName, None)
        return True

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
    def _getNormalEmojis(self, guildEmojis) -> Dict[str, Emoji]:
        normalEmojis = {}

        for emoji in guildEmojis:
            if emoji.name in cfg.DEFAULT_ROLES[self.platoon_size]:
                normalEmojis[emoji.name] = emoji

        return normalEmojis

    def getReactions(self) -> List[Emoji]:
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

        if self.sideop:
            if cfg.ATTENDANCE_EMOJI:
                reactions.append(cfg.ATTENDANCE_EMOJI)

        return reactions

    def countReactions(self) -> int:
        """Count how many reactions a message should have."""
        return len(self.getReactions())

    def getReactionsOfGroup(self, groupName: str) -> List[Emoji]:
        """Find reactions of a given role group."""
        reactions = []

        if groupName in self.roleGroups:
            for role in self.roleGroups[groupName].roles:
                reactions.append(role.emoji)

        return reactions

    def findRoleWithEmoji(self, emoji) -> Optional[Role]:
        """Find a role with given emoji."""
        for roleGroup in self.roleGroups.values():
            for role in roleGroup.roles:
                if role.emoji == emoji:
                    return role
        return None

    def findRoleWithName(self, roleName: str) -> Optional[Role]:
        """Find a role with given name."""
        roleName = roleName.lower()
        for roleGroup in self.roleGroups.values():
            role: Role
            for role in roleGroup.roles:
                if role.name.lower() == roleName:
                    return role
        return None

    def hasRoleGroup(self, groupName: str) -> bool:
        """Check if a role group with given name exists in the event."""
        return groupName in self.roleGroups

    def signup(self, roleToSet, user) -> Optional[List[Tuple[User, Role]]]:
        """Add username to role.

        Returns a tuple containing the role current user was removed from and
        the sign-up that this command replaced."""
        old_role = self.undoSignup(user)
        old_user = None
        for roleGroup in self.roleGroups.values():
            for role in roleGroup.roles:
                if role == roleToSet:
                    old_user = User(role.userID, role.userName)
                    role.userID = user.id
                    role.userName = user.display_name
                    return old_role, old_user
        return old_role, User()

    def undoSignup(self, user) -> Optional[Role]:
        """Remove username from any signups.

        Returns Role if user was signed up, otherwise None."""
        for roleGroup in self.roleGroups.values():
            for role in roleGroup.roles:
                if role.userID == user.id:
                    role.userID = None
                    role.userName = ""
                    return role

    def findSignupRole(self, userID) -> Optional[Role]:
        """Check if given user is already signed up."""
        for roleGroup in self.roleGroups.values():
            for role in roleGroup.roles:
                if role.userID == int(userID):
                    return role
        return None

    def __str__(self):
        return "{} (ID {}) at {}".format(self.title, self.id, self.date)

    def __repr__(self):
        return "<Event title='{}' id={} date='{}'>".format(
            self.title, self.id, self.date)

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
        data["messageID"] = self.messageID
        data["additionalRoleCount"] = self.additionalRoleCount
        data["platoon_size"] = self.platoon_size
        data["sideop"] = self.sideop
        data["roleGroups"] = roleGroupsData
        return data

    def fromJson(self, eventID, data, emojis):
        self.id = int(eventID)
        self.setTitle(data.get("title", TITLE))
        time = datetime.strptime(data.get("time", "00:00"), "%H:%M")
        self.setTime(time)
        self.setTerrain(data.get("terrain", TERRAIN))
        self.faction = data.get("faction", FACTION)
        self.description = data.get("description", DESCRIPTION)
        self.color = data.get("color", COLOR)
        self.messageID = data.get("messageID", 0)
        self.additionalRoleCount = data.get("additionalRoleCount", 0)
        self.platoon_size = data.get("platoon_size", PLATOON_SIZE)
        self.sideop = data.get("sideop", False)
        # TODO: Handle missing roleGroups
        for groupName, roleGroupData in data["roleGroups"].items():
            roleGroup = RoleGroup(groupName)
            roleGroup.fromJson(roleGroupData, emojis)
            self.roleGroups[groupName] = roleGroup
