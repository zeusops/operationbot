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
            if user == self.bot.user \
                    or reaction.message.channel.id != cfg.EVENT_CHANNEL:
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

            # Undo previous signup
            reactedEvent.undoSignup(user.display_name)

            # Update event
            reactedEvent.signup(role_, user.display_name)
            await self.eventDatabase.updateEvent(reaction.message,
                                                 reactedEvent)

            # Remove other emotes
            for reaction_ in reaction.message.reactions:
                if reaction_ != reaction:
                    users = await reaction_.users().flatten()
                    if user in users:
                        await reaction_.message.remove_reaction(reaction_,
                                                                user)

        @self.bot.event
        async def on_reaction_remove(reaction, user):
            # Exit if reaction is from bot or not in event channel
            if user == self.bot.user \
                    or reaction.message.channel.id != cfg.EVENT_CHANNEL:
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

            # Undo signup
            reactedEvent.undoSignup(user.display_name)

            # Update event
            await self.eventDatabase.updateEvent(reaction.message,
                                                 reactedEvent)


def setup(bot):
    importlib.reload(event)
    importlib.reload(cfg)
    bot.add_cog(EventListener(bot))
