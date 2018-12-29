import discord
import role
import config as cfg


class Event:

    def __init__(self, title, date, color, guildEmojis):
        self.title = title
        self.date = date
        self.color = color
        self.roles = {}
        self.additionalRoleCount = 0
        self.normalEmojis = self.getNormalEmojis(guildEmojis)
        self.addDefaultRoles()

    # Return an embed for the event
    def createEmbed(self, date):
        eventEmbed = discord.Embed(title=self.title, description=self.date,
                                   colour=self.color)
        enter = "\n"
        platoonRoles = ""
        additionalRoles = ""

        # Fill groups
        for role_, group in self.roles.items():
            if group == "platoon":
                platoonRoles += str(role_.emote) + enter

            if group == "additional":
                additionalRoles += str(role_.emote) + role_.name + enter

        # Create embed fields
        eventEmbed.add_field(name="Platoon Roles", value=platoonRoles,
                             inline=True)
        if len(additionalRoles) > 0:
            eventEmbed.add_field(name="Additional Roles",
                                 value=additionalRoles, inline=True)

        return eventEmbed

    # Add default
    def addDefaultRoles(self):
        for emoteName, emote in self.normalEmojis.items():
            newRole = role.Role(emoteName, emote)
            self.roles[newRole] = "platoon"

    # Add an additional role to the event
    def addAdditionalRole(self, name):
        # Find next emote for additional role
        emote = cfg.ADDITIONAL_ROLE_EMOTES[self.additionalRoleCount]

        # Create role
        newRole = role.Role(name, emote)

        # Add role to roles
        self.roles[newRole] = "additional"
        self.additionalRoleCount += 1

    # Get emojis for normal roles
    def getNormalEmojis(self, guildEmojis):
        normalEmojis = {}

        for emoji in guildEmojis:
            if emoji.name in cfg.NORMAL_ROLE_EMOTE_NAMES:
                normalEmojis[emoji.name] = emoji

        return normalEmojis
