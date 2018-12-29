import importlib
import event
import config as cfg
from main import eventDatabase


class EventListener:

    def __init__(self, bot):
        self.bot = bot
        self.eventDatabase = eventDatabase

        # Create event command
        @self.bot.event
        async def on_reaction_add(reaction, user):
            if user == self.bot.user:
                return

            print("me", reaction.me)

            print("beepboop")
            try:
                reactedEvent = self.eventDatabase \
                               .findEvent(reaction.message.id)
            except Exception:
                print("No event found with that message ID")
                return

            role = reaction.emoji.name

            print("event", reactedEvent)
            print("user", user.name, "role", role)
            channel = reaction.message.channel
            # TODO: Actually edit the event instead of just printing
            await channel.send("{} signed up for a role {} on an event {}"
                               .format(user.name, role, reactedEvent))

        @self.bot.event
        async def on_reaction_remove(reaction, user):
            if user == self.bot.user:
                return

            print("boopbeep")


def setup(bot):
    importlib.reload(event)
    importlib.reload(cfg)
    bot.add_cog(EventListener(bot))
