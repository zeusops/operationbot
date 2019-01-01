import config as cfg


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

        roleString += " " + self.user + "\n"

        return roleString

    def toJson(self):
        data = {}
        data["name"] = self.name
        data["displayName"] = self.displayName
        data["user"] = self.user

        if (type(self.emoji) is str):
            data["emoji"] = cfg.ADDITIONAL_ROLE_EMOJIS.index(self.emoji)
        else:
            data["emoji"] = self.emoji.name
        return data

    def fromJson(self, data):
        self.user = data["user"]
