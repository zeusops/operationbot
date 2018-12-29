class RoleGroup:

    def __init__(self, name):
        self.name = name
        self.roles = []

    def addRole(self, role):
        self.roles.append(role)

    def toString(self):
        roleGroupString = ""

        for role in self.roles:
            roleGroupString += role.toString()

        return roleGroupString
