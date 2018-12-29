import importlib
from discord.ext import commands
import event
import eventDatabase
import config as cfg


class CommandListener:

    def __init__(self, bot):
        self.bot = bot
        self.eventDatabase = eventDatabase.EventDatabase()

    # Create event command
    @commands.command(pass_context=True, name="create", brief="")
    async def createEvent(self, ctx):
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")

        # Exit if not enough info
        if (len(info) < 2):
            await ctx.send("No date specified")
            return

        # Get event data
        date = info[1]
        eventchannel = self.bot.get_channel(cfg.EVENT_CHANNEL)

        # Create event
        await self.eventDatabase.createEvent(date, ctx.guild.emojis, eventchannel)

    # Add additional role to event command
    @commands.command(pass_context=True, name="addrole", brief="")
    async def addRole(self, ctx):
        # Get info from context
        info = ctx.message.content
        info = info.split(" ")

        # Get eventchannel
        eventchannel = self.bot.get_channel(cfg.EVENT_CHANNEL)

        # Get data
        try:
            messageID = int(info[1])
        except Exception:
            await ctx.send("Invalid message ID, needs to be an integer")
            return

        # Get roleName
        roleName = ""
        for word in info[2:]:
            roleName += " " + word

        # Get message, return if not found
        try:
            eventMessage = await eventchannel.get_message(messageID)
        except Exception:
            await ctx.send("No message found with that message ID")
            return
        
        # Find event with messageID
        try:
            event = self.eventDatabase.findEvent(messageID)
        except Exception:
            await ctx.send("No event found with that message ID")
            return

        # Update event
        event.addAdditionalRole(roleName)
        await self.eventDatabase.updateEvent(eventMessage, event)

def setup(bot):
    importlib.reload(event)
    importlib.reload(cfg)
    bot.add_cog(CommandListener(bot))
