import json
import os
from datetime import datetime
from typing import Dict, Tuple

from discord import Message, TextChannel
from discord.ext.commands import Bot

import config as cfg
from event import Event


class EventDatabase:

    def __init__(self):
        self.events: Dict[int, Event] = {}
        self.eventsArchive: Dict[int, Event] = {}

    # Create a new event and store it
    async def createEvent(self, date: datetime,
                          channel: TextChannel) -> Tuple[Message, Event]:
        # Create event
        newEvent = Event(date, channel.guild.emojis)

        # Create message
        newEventMessage = await self.createEventMessage(newEvent, channel)

        # Store event
        self.events[newEventMessage.id] = newEvent

        return newEventMessage, newEvent

    # Create a new event message
    async def createEventMessage(self, event: Event,
                                 channel: TextChannel) -> Message:
        # Create embed and message
        newEventEmbed = event.createEmbed()
        newEventMessage = await channel.send(embed=newEventEmbed)

        # Put message ID in footer
        newEventEmbed = newEventMessage.embeds[0]
        newEventEmbed.set_footer(text="Message ID: " + str(newEventMessage.id))
        await newEventMessage.edit(embed=newEventEmbed)

        return newEventMessage

    # Move event to archive
    async def archiveEvent(self, eventmessage: Message, event: Event,
                           eventarchivechannel: TextChannel):
        # Remove event from events
        await self.removeEvent(eventmessage)

        # Create new message
        newEventMessage = await self.createEventMessage(event,
                                                        eventarchivechannel)

        # Add event to eventsArchive
        self.eventsArchive[newEventMessage.id] = event

    # Update an existing event and store it
    async def updateEvent(self, eventMessage: Message, updatedEvent: Event):
        newEventEmbed = updatedEvent.createEmbed()
        newEventEmbed.set_footer(text="Message ID: " + str(eventMessage.id))
        await eventMessage.edit(embed=newEventEmbed)

        # Store event
        self.events[eventMessage.id] = updatedEvent

    # Remove event
    async def removeEvent(self, eventmessage: Message):
        if eventmessage.id in self.events.keys():
            del self.events[eventmessage.id]
            await eventmessage.delete()

    # Remove event from archive
    async def removeEventFromArchive(self, eventmessage: Message):
        if eventmessage.id in self.eventsArchive.keys():
            del self.eventsArchive[eventmessage.id]
            await eventmessage.delete()

    # Find an event with it's message ID
    def findEvent(self, messageID: int) -> Event:
        return self.events.get(messageID)

    def findEventInArchive(self, messageID: int):
        return self.eventsArchive.get(messageID)

    def sortEvents(self):
        messageIDs = []
        events = []

        # Store existing events
        for messageID, event in self.events.items():
            messageIDs.append(messageID)
            events.append(event)

        # Sort events based on date and time
        events.sort(key=lambda event: event.date, reverse=True)

        # Fill events again
        index = 0
        self.events = {}
        for messageID in messageIDs:
            self.events[messageID] = events[index]
            index += 1

    async def updateReactions(self, message: Message, event: Event, bot: Bot):
        reactionEmojisIntended = event.getReactions()
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
            await message.remove_reaction(reaction, bot.user)

        # Add not existing intended emojis
        for emoji in reactionEmojisToAdd:
            await message.add_reaction(emoji)

    def toJson(self):
        # Get eventsData
        eventsData = {}
        for messageID, event in self.events.items():
            eventsData[messageID] = event.toJson()

        # Get eventsArchiveData
        eventsArchiveData = {}
        for messageID, event in self.eventsArchive.items():
            eventsArchiveData[messageID] = event.toJson()

        # Store data and return
        data = {}
        data["events"] = eventsData
        data["eventsArchive"] = eventsArchiveData

        with open(cfg.JSON_FILEPATH, "w") as jsonFile:
            json.dump(data, jsonFile, indent=2)

    # Fills events and eventsArchive with data from JSON
    async def fromJson(self, bot: Bot):
        # Import
        try:
            try:
                with open(cfg.JSON_FILEPATH) as jsonFile:
                    data = json.load(jsonFile)
            except json.decoder.JSONDecodeError:
                print("Malformed JSON file! Backing up and",
                      "creating an empty database")
                # Backup old file
                backupName = "{}-{}.bak" \
                    .format(cfg.JSON_FILEPATH,
                            datetime.now().strftime(
                                '%Y-%m-%dT%H-%M-%S'))
                os.rename(cfg.JSON_FILEPATH, backupName)
                print("Backed up to", backupName)
                # Let next handler create the file and continue importing
                raise FileNotFoundError
        except FileNotFoundError:
            print("JSON not found, creating")
            with open(cfg.JSON_FILEPATH, "w") as jsonFile:
                # Create a new file with empty JSON structure inside
                json.dump({"events": {}, "eventsArchive": {}}, jsonFile,
                          indent=2)
            # Try to import again
            await self.fromJson(bot)
            return

        self.events = {}
        self.eventsArchive = {}
        eventsData = data["events"]
        eventsArchiveData = data["eventsArchive"]
        eventchannel = bot.get_channel(cfg.EVENT_CHANNEL)

        # Clear events channel
        if cfg.PURGE:
            await eventchannel.purge(limit=100)

        # Add events
        for messageID, eventData in eventsData.items():
            # Create event
            date = datetime.strptime(eventData["date"],
                                     '%Y-%m-%d')
            eventMessage, event = await self.createEvent(date,
                                                         eventchannel)
            event.fromJson(eventData, eventchannel.guild)
            await self.updateEvent(eventMessage, event)

        # Add reactions to events
        for messageID, event in self.events.items():
            eventmessage = await eventchannel.fetch_message(messageID)
            await self.updateReactions(eventmessage, event, bot)

        # Add archived events
        for messageID, eventData in eventsArchiveData.items():
            # Create event
            date = datetime.strptime(eventData["date"], "%Y-%m-%d")
            event = Event(date, eventchannel.guild.emojis)
            event.fromJson(eventData, eventchannel.guild)
            self.eventsArchive[messageID] = event

        for messageID, event in self.events.items():
            print(messageID, event)
