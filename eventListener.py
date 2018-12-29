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
            # Exit if reaction is from bot or not in event channel
            if user == self.bot.user or reaction.message.channel == cfg.EVENT_CHANNEL:
                return

            # Get event from database with message ID
            try:
                reactedEvent = self.eventDatabase \
                               .findEvent(reaction.message.id)
            except Exception:
                print("No event found with that message ID")
                return

            # Get emoji string
            emoji = reaction.emoji

            # Get role with the emoji
            role_ = reactedEvent.findRole(emoji)
            if role_ is None:
                print("No role found with that emoji")
                return

            # Update event
            reactedEvent.setRole(role_, user.display_name)
            await self.eventDatabase.updateEvent(reaction.message, reactedEvent)

        @self.bot.event
        async def on_reaction_remove(reaction, user):
            if user == self.bot.user:
                return

            print("boopbeep")


def setup(bot):
    importlib.reload(event)
    importlib.reload(cfg)
    bot.add_cog(EventListener(bot))
