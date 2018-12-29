class Role:

    def __init__(self, name, emoji):
        self.name = name
        self.emoji = emoji
        self.user = ""

    def setUser(self, user):
        self.user = user
