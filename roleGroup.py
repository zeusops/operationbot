class RoleGroup:

    def __init__(self, name):
        self.name = name
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
