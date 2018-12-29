import discord
import role
import roleGroup
import config as cfg


class Event:

    def __init__(self, date, guildEmojis):
        self.title = "Operation"
        self.date = date
        self.color = 0xFF4500
        self.roleGroups = {}
        self.additionalRoleCount = 0

        self.normalEmojis = self.getNormalEmojis(guildEmojis)
        self.addDefaultRoleGroups()
        self.addDefaultRoles()

    # Return an embed for the event
    def createEmbed(self):
        eventEmbed = discord.Embed(title=self.title, description=self.date,
                                   colour=self.color)

        # Add field to embed for every rolegroup
        for group in self.roleGroups.values():
            if len(group.roles) > 0:
                eventEmbed.add_field(name=group.name, value=str(group),
                                     inline=True)

        return eventEmbed

    # Add default role groups
    def addDefaultRoleGroups(self):
        platoonGroup = roleGroup.RoleGroup("Platoon")
        alphaGroup = roleGroup.RoleGroup("Alpha")
        bravoGroup = roleGroup.RoleGroup("Bravo")
        additionalGroup = roleGroup.RoleGroup("Additional")

        self.roleGroups["Platoon"] = platoonGroup
        self.roleGroups["Alpha"] = alphaGroup
        self.roleGroups["Bravo"] = bravoGroup
        self.roleGroups["Additional"] = additionalGroup

    # Add default roles
    def addDefaultRoles(self):
        for name, groupName in cfg.DEFAULT_ROLES.items():
            # Only add role if the group exists
            if groupName in self.roleGroups.keys():
                emoji = self.normalEmojis[name]
                newRole = role.Role(name, emoji, False)
                self.roleGroups[groupName].addRole(newRole)

    # Add an additional role to the event
    def addAdditionalRole(self, name):
        # Find next emoji for additional role
        emoji = cfg.ADDITIONAL_ROLE_EMOJIS[self.additionalRoleCount]

        # Create role
        newRole = role.Role(name, emoji, True)

        # Add role to roles
        self.roleGroups["Additional"].addRole(newRole)
        self.additionalRoleCount += 1

        return emoji

    # Get emojis for normal roles
    def getNormalEmojis(self, guildEmojis):
        normalEmojis = {}

        for emoji in guildEmojis:
            if emoji.name in cfg.DEFAULT_ROLES:
                normalEmojis[emoji.name] = emoji

        return normalEmojis

    # Returns reactions of all roles
    def getReactions(self):
        reactions = []

        for roleGroup_ in self.roleGroups.values():
            for role_ in roleGroup_.roles:
                reactions.append(role_.emoji)

        return reactions

    # Find role with emoji
    def findRole(self, emoji):
        for roleGroup_ in self.roleGroups.values():
            for role_ in roleGroup_.roles:
                if role_.emoji == emoji:
                    return role_

    # Add username to role
    def signup(self, roleToSet, username):
        for roleGroup_ in self.roleGroups.values():
            for role_ in roleGroup_.roles:
                if role_ == roleToSet:
                    role_.user = username

    # Remove username from any signups
    def undoSignup(self, username):
        for roleGroup_ in self.roleGroups.values():
            for role_ in roleGroup_.roles:
                if role_.user == username:
                    role_.user = ""
                    return role_.emoji
        return None

    # Returns if given user is already signed up
    def findSignup(self, username):
        for roleGroup_ in self.roleGroups.values():
            for role_ in roleGroup_.roles:
                if role_.user == username:
                    return role_
        return None

    def __str__(self):
        return "{} at {}".format(self.title, self.date)
