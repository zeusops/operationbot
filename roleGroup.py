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
