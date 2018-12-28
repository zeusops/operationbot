import discord
import sqlite3

from discord.ext import commands

class AddRole:

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, name="addrole", brief="")
    async def addRole(self, ctx):
        info = ctx.message.content
        info = info.split(" ")

        eventID = info[1]
        roleL = info[2:]
        role = ""
        for word in roleL:
            role += word + " "

        eventchannel = self.bot.get_channel(502824760036818964)

        try:
            event = await eventchannel.get_message(int(eventID))
        except:
            await ctx.send("That event does not exist.")
            return

        em = event.embeds[0]

        fields = em.fields
        for field in fields:
            if field.name == "Additional Roles":
                additionalRoles = field.value + " \n" + str(role)
                em.remove_field(3)
            else:
                additionalRoles =  ":one: " + role
                await event.add_reaction(emoji=":one:")

        otherRoles = additionalRoles.split("\n")
        number = len(otherRoles)
        await ctx.send(number)

        em.add_field(name="Additional Roles", value=additionalRoles)
        await event.edit(embed=em)

def setup(bot):
    bot.add_cog(AddRole(bot))