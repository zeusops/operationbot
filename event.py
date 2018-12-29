import discord
import role
import roleGroup
import config as cfg


class Event:

    def __init__(self, title, date, color, guildEmojis):
        self.title = title
        self.date = date
        self.color = color
        self.roleGroups = {}
        self.additionalRoleCount = 0

        self.normalEmojis = self.getNormalEmojis(guildEmojis)
        self.addDefaultRoleGroups()
        self.addDefaultRoles()

    # Return an embed for the event
    def createEmbed(self, date):
        eventEmbed = discord.Embed(title=self.title, description=self.date, colour=self.color)

        # Add field to embed for every rolegroup
        for groupName, group in self.roleGroups.items():
            if len(group.roles) > 0:
                eventEmbed.add_field(name=group.name, value=group.toString(), inline=True)

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
                newRole = role.Role(name, emoji)
                self.roleGroups[groupName].addRole(newRole)

    # Add an additional role to the event
    def addAdditionalRole(self, name):
        # Find next emoji for additional role
        emoji = cfg.ADDITIONAL_ROLE_EMOJIS[self.additionalRoleCount]

        # Create role
        newRole = role.Role(name, emoji)

        # Add role to roles
        self.roleGroups["Additional"].addRole(newRole)
        self.additionalRoleCount += 1

    # Get emojis for normal roles
    def getNormalEmojis(self, guildEmojis):
        normalEmojis = {}

        for emoji in guildEmojis:
            if emoji.name in cfg.DEFAULT_ROLES:
                normalEmojis[emoji.name] = emoji

        return normalEmojis
