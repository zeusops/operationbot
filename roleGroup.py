class RoleGroup:

    def __init__(self, name):
        self.name = name
        self.roles = []

    def addRole(self, role):
        self.roles.append(role)

    def __str__(self):
        # TODO: use __str__
        roleGroupString = ""

        for role in self.roles:
            roleGroupString += str(role)

        return roleGroupString
