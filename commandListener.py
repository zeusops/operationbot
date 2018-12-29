import importlib
from discord.ext import commands

import event
import config as cfg


class CommandListener:

    def __init__(self, bot):
        self.bot = bot

    # Create event command
    @commands.command(pass_context=True, name="create", brief="")
    async def createEvent(self, ctx):
        # Get into from context
        info = ctx.message.content
        info = info.split(" ")

        # Exit if not enough info
        if (len(info) < 2):
            await ctx.send("No date specified")
            return

        # Get event data
        title = "Operation"
        date = info[1]
        color = 0xFF4500
        eventchannel = self.bot.get_channel(cfg.EVENT_CHANNEL)
        thing = (ctx.guild.emojis[46])

        # Create event
        newEvent = event.Event(title, date, color, ctx.guild.emojis)
        newEventEmbed = newEvent.createEmbed(date)
        newEventMessage = await eventchannel.send(embed=newEventEmbed)

        # Put message ID in footer
        newEventEmbed = newEventMessage.embeds[0]
        newEventEmbed.set_footer(text="Message ID: " + str(newEventMessage.id))
        await newEventMessage.edit(embed=newEventEmbed)

        # Add reactions
        await newEventMessage.add_reaction(thing)

    # Add additional role to event command
    @commands.command(pass_context=True, name="addrole", brief="")
    async def addRole(self, ctx):
        # Get into from context
        info = ctx.message.content
        info = info.split(" ")

        # Get data
        eventID = info[1]
        # roleList = info[2:]
        role = ""
        for word in info:
            role += word + " "

        eventchannel = self.bot.get_channel(cfg.BOT_CHANNEL)

        try:
            eventMessage = await eventchannel.get_message(int(eventID))
        except Exception:
            await ctx.send("That event does not exist.")
            return

        eventEmbed = eventMessage.embeds[0]

        fields = eventEmbed.fields
        for field in fields:
            if field.name == "Additional Roles":
                additionalRoles = field.value + " \n" + str(role)
                eventEmbed.remove_field(3)
            else:
                additionalRoles = ":one: " + role
                await eventMessage.add_reaction(emoji=":one:")

        otherRoles = additionalRoles.split("\n")
        number = len(otherRoles)
        await ctx.send(number)

        eventEmbed.add_field(name="Additional Roles", value=additionalRoles)
        await eventMessage.edit(embed=eventEmbed)


def setup(bot):
    importlib.reload(event)
    bot.add_cog(CommandListener(bot))
