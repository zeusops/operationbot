import importlib
import event
import config as cfg


class EventListener:

    def __init__(self, bot):
        self.bot = bot

        # Create event command
        @self.bot.event
        async def on_reaction_add(reaction, user):
            if user == self.bot.user:
                return

            print("beepboop")

        @self.bot.event
        async def on_reaction_remove(reaction, user):
            if user == self.bot.user:
                return

            print("boopbeep")


def setup(bot):
    importlib.reload(event)
    importlib.reload(cfg)
    bot.add_cog(EventListener(bot))
