import json
import event
import config as cfg


class EventDatabase:

    def __init__(self):
        self.events = {}
        self.eventsArchive = {}

    # Create a new event and store it
    async def createEvent(self, date, channel):
        # Create event
        newEvent = event.Event(date, channel.guild.emojis)

        # Create message
        newEventMessage = await self.createEventMessage(newEvent, channel)

        # Store event
        self.events[newEventMessage.id] = newEvent

        return newEventMessage, newEvent

    # Create a new event message
    async def createEventMessage(self, event_, channel):
        # Create embed and message
        newEventEmbed = event_.createEmbed()
        newEventMessage = await channel.send(embed=newEventEmbed)

        # Put message ID in footer
        newEventEmbed = newEventMessage.embeds[0]
        newEventEmbed.set_footer(text="Message ID: " + str(newEventMessage.id))
        await newEventMessage.edit(embed=newEventEmbed)

        return newEventMessage

    # Move event to archive
    async def archiveEvent(self, eventmessage, event_, eventchannel,
                           eventarchivechannel):
        # Remove event from events
        await self.removeEvent(eventmessage)

        # Create new message
        newEventMessage = await self.createEventMessage(event_,
                                                        eventarchivechannel)

        # Add event to eventsArchive
        self.eventsArchive[newEventMessage.id] = event_

    # Update an existing event and store it
    async def updateEvent(self, eventMessage, updatedEvent):
        newEventEmbed = updatedEvent.createEmbed()
        newEventEmbed.set_footer(text="Message ID: " + str(eventMessage.id))
        await eventMessage.edit(embed=newEventEmbed)

        # Store event
        self.events[eventMessage.id] = updatedEvent

    # Remove event
    async def removeEvent(self, eventmessage):
        if eventmessage.id in self.events.keys():
            del self.events[eventmessage.id]
            await eventmessage.delete()

    # Remove event from archive
    async def removeEventFromArchive(self, eventmessage):
        if eventmessage.id in self.eventsArchive.keys():
            del self.eventsArchive[eventmessage.id]
            await eventmessage.delete()

    # Find an event with it's message ID
    def findEvent(self, messageID):
        if messageID in self.events.keys():
            return self.events[messageID]

    def findEventInArchive(self, messageID):
        if messageID in self.eventsArchive.keys():
            return self.eventsArchive[messageID]

    # Add given reaction to given message
    async def addReaction(self, eventMessage, reaction):
        await eventMessage.add_reaction(reaction)

    async def removeReaction(self, eventMessage, reaction, user):
        await eventMessage.remove_reaction(reaction, user)

    def sortEvents(self):
        messageIDs = []
        events = []

        # Store existing events
        for messageID, event_ in self.events.items():
            messageIDs.append(messageID)
            events.append(event_)

        # Sort events based on date and time
        events.sort(key=lambda event: event.date, reverse=True)

        # Fill events again
        index = 0
        self.events = {}
        for messageID in messageIDs:
            self.events[messageID] = events[index]
            index += 1

    async def updateReactions(self, message_, event_, bot):
        reactionEmojisIntended = event_.getReactions()
        reactionsCurrent = message_.reactions
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
            await self.removeReaction(message_, reaction, bot.user)

        # Add not existing intended emojis
        for emoji in reactionEmojisToAdd:
            await self.addReaction(message_, emoji)

    def toJson(self):
        # Get eventsData
        eventsData = {}
        for messageID, event_ in self.events.items():
            eventsData[messageID] = event_.toJson()

        # Get eventsArchiveData
        eventsArchiveData = {}
        for messageID, event_ in self.eventsArchive.items():
            eventsData[messageID] = event_.toJson()

        # Store data and return
        data = {}
        data["events"] = eventsData
        data["eventsArchive"] = eventsArchiveData

        with open(cfg.JSON_FILEPATH, "w") as jsonFile:
            json.dump(data, jsonFile)

    # Fills events and eventsArchive with data from JSON
    async def fromJson(self, bot):
        # Import
        with open(cfg.JSON_FILEPATH) as jsonFile:
            data = json.load(jsonFile)

        self.events = {}
        self.eventsArchive = {}
        eventsData = data["events"]
        eventsArchiveData = data["eventsArchive"]
        eventchannel = bot.get_channel(cfg.EVENT_CHANNEL)

        # Clear events channel
        await eventchannel.purge(limit=100)

        # Add events
        for messageID, eventData in eventsData.items():
            # Create event
            eventMessage_, event_ = await self.createEvent(eventData["date"],
                                                           eventchannel)
            event_.fromJson(eventData, eventchannel.guild)
            await self.updateEvent(eventMessage_, event_)

        # Add reactions to events
        for messageID, event_ in self.events.items():
            eventmessage = await eventchannel.get_message(messageID)
            await self.updateReactions(eventmessage, event_, bot)

        # Add archived events
        for messageID, eventData in eventsArchiveData.items():
            # Create event
            event_ = event.Event(eventsArchiveData["date"],
                                 eventchannel.guild.emojis)
            event_.fromJson(eventData, eventchannel.guild)
            self.eventsArchive[messageID] = event_

        for messageID, event_ in self.events.items():
            print(messageID, event_)
