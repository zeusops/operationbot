from typing import Optional, Union

from discord import Emoji


class Role:

    def __init__(self, name: str, emoji: Union[str, Emoji], displayName: bool):
        self.name = name
        self.emoji = emoji
        self.displayName = displayName
        self.userID: Optional[int] = None
        self.userName = ""

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
        return data

    def fromJson(self, data: dict):
        self.userID = data["userID"]
        self.userName = data["userName"]
