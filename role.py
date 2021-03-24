from typing import Optional, Union

from discord import Emoji


class Role:

    def __init__(self, name: str, emoji: Union[str, Emoji], show_name: bool):
        self.name = name
        self.emoji = emoji
        self.show_name = show_name
        self.userID: Optional[int] = None
        self.userName = ""

    def __str__(self):
        # Add name after emote if it should display
        if self.show_name:
            return "{} {}: {}\n".format(str(self.emoji),
                                        self.name,
                                        self.userName)
        else:
            return "{} {}\n".format(str(self.emoji), self.userName)

    def __repr__(self):
        return "<Role name='{}' userName='{}'>".format(self.name, self.userName)

    def toJson(self, brief_output=False):
        data = {}
        if not brief_output or self.show_name:
            # Name is displayed when exporting full data (not brief_output) or
            # when role is an additional role (show_name is set)
            data["name"] = self.name
        if not brief_output:
            # These are not relevant when exporting brief data
            data["show_name"] = self.show_name
            data["userID"] = self.userID
        data["userName"] = self.userName
        return data

    def fromJson(self, data: dict, manual_load=False):
        name = data.get("name")
        if name:
            # The brief output of main roles does not have the "name" field,
            # will only change name if it is actually set in the source data
            self.name = name
        if not manual_load:
            self.userID = data["userID"]
            self.userName = data["userName"]
