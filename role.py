class Role:

    def __init__(self, name, emoji, displayName):
        self.name = name
        self.emoji = emoji
        self.displayName = displayName
        self.user = ""

    def setUser(self, user):
        self.user = user

    def __str__(self):
        roleString = str(self.emoji)

        # Add name after emote if it should display
        if self.displayName:
            roleString += self.name + ":"
        # TODO: Check if a space before the username is necessary
        # (depends on input function)
        roleString += " " + self.user + "\n"

        return roleString

    def toJson(self):
        data = {}
        data["name"] = self.name
        data["emoji"] = self.emoji.name
        data["displayName"] = self.displayName
        data["user"] = self.user
        return data
