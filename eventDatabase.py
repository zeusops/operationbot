import event


class EventDatabase:

    def __init__(self):
        self.events = {}
        self.eventsArchive = {}

    # Create a new event and store it
    async def createEvent(self, date, guildEmojis, eventchannel):
        # Create event
        newEvent = event.Event(date, guildEmojis)

        # Create message
        newEventMessage = await self.createEventMessage(newEvent, eventchannel)

        # Add reactions
        reactions = newEvent.getReactions()
        for reaction in reactions:
            await self.addReaction(newEventMessage, reaction)

        # Store event
        self.events[newEventMessage.id] = newEvent

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
        del self.events[eventmessage.id]

        # Remove old message
        await eventmessage.delete()

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

    # Find an event with it's message ID
    def findEvent(self, messageID):
        if messageID in self.events:
            return self.events[messageID]
        else:
            raise Exception

    # Add given reaction to given message
    async def addReaction(self, eventMessage, reaction):
        # try:
            await eventMessage.add_reaction(reaction)
        # TODO: catch only discord API related errors
        # except Exception:
        #     print("Emote " + str(reaction) + " is unknown", type(reaction))
        #     return
