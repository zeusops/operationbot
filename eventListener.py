import importlib
import event
import eventDatabase
import config as cfg


class EventListener:

    def __init__(self, bot):
        self.bot = bot

        # Create event command
        @bot.event
        async def on_reaction_add(reaction, user):
            print("beepboop")

def setup(bot):
    importlib.reload(event)
    importlib.reload(cfg)
    bot.add_cog(EventListener(bot))
