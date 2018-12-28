import discord
import sqlite3

from discord.ext import commands

class EventCreate:

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, name="create", brief="")
    async def createEvent(self, ctx):
        info = ctx.message.content
        info = info.split(" ")

        eventchannel = self.bot.get_channel(502824760036818964)

        try:
            date = info[1]
        except:
            pass

        thing = (ctx.guild.emojis[46])

        em = discord.Embed(title=("Operation"), description="(" + str(date) + ")", colour=0xFF4500)

        em.add_field(name="Platoon Roles", value="HQ1PLT: \n"
                                                 "RTO: \n"
                                                 "FAC: ", inline=True)
        em.add_field(name="Alpha Leading Roles", value=str(thing) + "ASL: \n"
                                                 "A1: \n"
                                                 "A2", inline=True)
        em.add_field(name="Bravo Leading Roles", value="BSL: \n"
                                                 "B1: \n"
                                                 "B2: ", inline=True)
        event = await eventchannel.send(embed=em)

        await event.add_reaction(thing)
        em = event.embeds[0]
        em.set_footer(text="Event ID: " + str(event.id))
        await event.edit(embed=em)

def setup(bot):
    bot.add_cog(EventCreate(bot))