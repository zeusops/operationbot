import event


class EventDatabase:

    def __init__(self):
        self.events = {}

    async def createEvent(self, date, guildEmojis, eventchannel):
        # Create event
        newEvent = event.Event(date, guildEmojis)
        newEventEmbed = newEvent.createEmbed()
        newEventMessage = await eventchannel.send(embed=newEventEmbed)

        # Put message ID in footer
        newEventEmbed = newEventMessage.embeds[0]
        newEventEmbed.set_footer(text="Message ID: " + str(newEventMessage.id))
        await newEventMessage.edit(embed=newEventEmbed)

        self.events[newEventMessage.id] = newEvent
        # Add reactions
        #await newEventMessage.add_reaction(thing)

    async def updateEvent(self, eventMessage, event):
        newEventEmbed = event.createEmbed()
        await eventMessage.edit(embed=newEventEmbed)

        self.events[eventMessage.id] = event

    def findEvent(self, messageID):
        if messageID in self.events:
            return self.events[messageID]
        else:
            raise Exception
