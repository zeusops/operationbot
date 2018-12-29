class Role:

    def __init__(self, name, emoji, displayName):
        self.name = name
        self.emoji = emoji
        self.displayName = displayName
        self.user = ""

    def setUser(self, user):
        self.user = user

    def toString(self):
        roleString = str(self.emoji)

        # Add name after emote if it should display
        if self.displayName:
            roleString += self.name + ":"

        roleString += " " + self.user + "\n" #TODO: Check if a space before the username is necessary (depends on input function)
        
        return roleString
