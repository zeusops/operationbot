import role
import config as cfg


class RoleGroup:

    def __init__(self, name, isInline):
        self.name = name
        self.isInline = isInline
        self.roles = []

    # Add role to the group
    def addRole(self, role_):
        self.roles.append(role_)

    # Remove role from the group
    def removeRole(self, roleName):
        for role_ in self.roles:
            if (role_.name == roleName):
                self.roles.remove(role_)

    def __str__(self):
        roleGroupString = ""

        for role_ in self.roles:
            roleGroupString += str(role_)

        return roleGroupString

    def toJson(self):
        rolesData = {}
        for role_ in self.roles:
            rolesData[role_.name] = role_.toJson()

        data = {}
        data["name"] = self.name
        data["isInline"] = self.isInline
        data["roles"] = rolesData
        return data

    def fromJson(self, data, ctx):
        self.name = data["name"]
        self.isInline = data["isInline"]
        for roleName, roleData in data["roles"].items():
            emoji = None
            if (type(roleData["emoji"]) is str):
                for emoji_ in ctx.guild.emojis:
                    if emoji_.name == roleData["emoji"]:
                        emoji = emoji_
                        break
            else:
                emoji = cfg.ADDITIONAL_ROLE_EMOJIS[roleData["emoji"]]
            role_ = role.Role(roleData["name"], emoji, roleData["displayName"])
            role_.fromJson(roleData)
            self.roles.append(role_)
