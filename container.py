from typing import List, Optional

from discord import Embed, Emoji, Message, NotFound, TextChannel

import config as cfg
from eventDatabase import EventDatabase
from event import Event
import messageFunctions as msgFnc


class Container():
    def __init__(self, event: Event, channel: TextChannel, message: Message):
        self.event = event
        self.channel = channel
        self.message = message
        self.id = message.id

    def __lt__(self, other):
        return self.id < other.id

    def __repr__(self):
        return "<Container id={0.id} event={0.event!r}>".format(self)

    @classmethod
    async def send(cls, event: Event, channel: TextChannel):
        # TODO: Check if actually necessary to have content
        message = await channel.send("\N{ZERO WIDTH SPACE}")
        self = Container(event, channel, message)

        event.container = self
        event.messageID = self.message.id
        await self.updateEmbed()
        return self

    # Return an embed for the event
    def _createEmbed(self) -> Embed:
        title = "{} ({})".format(
            self.event.title,
            self.event.date.strftime("%a %Y-%m-%d - %H:%M CEST"))
        description = "Terrain: {} - Faction: {}\n\n{}".format(
            self.event.terrain, self.event.faction, self.event.description)
        eventEmbed = Embed(title=title, description=description,
                           colour=self.event.color)

        # Add field to embed for every rolegroup
        for group in self.event.roleGroups.values():
            if len(group.roles) > 0:
                eventEmbed.add_field(name=group.name, value=str(group),
                                     inline=group.isInline)
            elif group.name == "Dummy":
                eventEmbed.add_field(name="\N{ZERO WIDTH SPACE}",
                                     value="\N{ZERO WIDTH SPACE}",
                                     inline=group.isInline)

        return eventEmbed

    # was: EventDatabase.updateEvent
    async def updateEmbed(self) -> None:
        """Update the embed and footer of a message."""
        embed = self._createEmbed()
        embed.set_footer(text="Event ID: " + str(self.event.id))
        await self.message.edit(embed=embed)

    async def getMessage(self, bot) -> Message:
        """Get a message related to an event."""
        if self.message is not None:
            return self.message
        else:
            return msgFnc.getEventMessage(self.event, bot)

    # from EventDatabase
    async def updateReactions(self, message: Message = None, bot=None):
        """
        Update reactions of an event message.

        Requires either container.message to be set or the `bot` argument to
        be provided.
        """
        if message is None:
            message = await self.getMessage(bot)
            if message is None and bot is None:
                raise ValueError("container.message not set. Requires the "
                                 "`bot` argument to be provided")

        reactions: List[Emoji] = self.event.getReactions()
        reactionEmojisIntended = [cfg.EMOJI_SIGNOFF] + reactions
        reactionsCurrent = message.reactions
        reactionEmojisCurrent = {}
        reactionsToRemove = []
        reactionEmojisToAdd = []

        # Find reaction emojis current
        for reaction in reactionsCurrent:
            reactionEmojisCurrent[reaction.emoji] = reaction

        # Find emojis to remove
        for emoji, reaction in reactionEmojisCurrent.items():
            if emoji not in reactionEmojisIntended:
                reactionsToRemove.append(reaction)

        # Find emojis to add
        for emoji in reactionEmojisIntended:
            if emoji not in reactionEmojisCurrent.keys():
                reactionEmojisToAdd.append(emoji)

        # Remove existing unintended reactions
        for reaction in reactionsToRemove:
            await message.clear_reaction(reaction)

        # Add not existing intended emojis
        for emoji in reactionEmojisToAdd:
            await message.add_reaction(emoji)

    def setEvent(self, event: Event):
        self.event = event
        self.event.container = self
        self.event.messageID = self.event.container.id

    @staticmethod
    def sortEvents():
        sortedEvents = []
        containers = []

        # Store existing events
        for event in EventDatabase.events.values():
            sortedEvents.append(event)
            containers.append(event.container)

        # Sort events based on date and time
        sortedEvents.sort(reverse=True)
        containers.sort(reverse=True)

        # Fill events again
        for event in sortedEvents:
            containers.pop().setEvent(event)
