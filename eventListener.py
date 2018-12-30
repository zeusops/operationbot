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

            # Remove the reaction
            await reaction.message.remove_reaction(reaction, user)

            # Get event from database with message ID
            try:
                reactedEvent = self.eventDatabase \
                               .findEvent(reaction.message.id)
            except Exception:
                print("No event found with that message ID")
                return

            # Get emoji string
            emoji = reaction.emoji

            # Find signup of user
            signup = reactedEvent.findSignup(user.display_name)

            # if user is not signed up, and the role is free, signup
            # if user is not signed up, and the role is not free, do nothing
            # if user is signed up, and he selects the same role, signoff
            # if user is signed up, and he selects a different role, do nothing
            if signup is None:
                # Get role with the emoji
                role_ = reactedEvent.findRoleWithEmoji(emoji)
                if role_ is None:
                    print("No role found with that emoji")
                    return

                # Sign up if role is free
                if role_.user == "":
                    # signup
                    reactedEvent.signup(role_, user.display_name)

                    # Update event
                    await self.eventDatabase.updateEvent(reaction.message,
                                                         reactedEvent)
            elif signup.emoji == emoji:
                # undo signup
                reactedEvent.undoSignup(user.display_name)

                # Update event
                await self.eventDatabase.updateEvent(reaction.message,
                                                     reactedEvent)

        # @self.bot.event
        # async def on_reaction_remove(reaction, user):


def setup(bot):
    importlib.reload(event)
    importlib.reload(cfg)
    bot.add_cog(EventListener(bot))
