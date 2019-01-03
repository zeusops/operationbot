import config as cfg


class Role:

    def __init__(self, name, emoji, displayName):
        self.name = name
        self.emoji = emoji
        self.displayName = displayName
        self.userID = None
        self.userName = ""

    def setUser(self, user):
        self.user = user

    def __str__(self):
        # Add name after emote if it should display
        if self.displayName:
            return "{} {}: {}\n".format(str(self.emoji),
                                        self.name,
                                        self.userName)
        else:
            return "{} {}\n".format(str(self.emoji), self.userName)

    def toJson(self):
        data = {}
        data["name"] = self.name
        data["displayName"] = self.displayName
        data["userID"] = self.userID
        data["userName"] = self.userName

        if (type(self.emoji) is str):
            data["emoji"] = cfg.ADDITIONAL_ROLE_EMOJIS.index(self.emoji)
        else:
            data["emoji"] = self.emoji.name
        return data

    def fromJson(self, data):
        self.userID = data["userID"]
        self.userName = data["userName"]
