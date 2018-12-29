import traceback

from discord.ext import commands
from main import initial_extensions


class Reload:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, name="reload", brief="")
    async def reloadBot(self, ctx):
        print("Reloading extensions")
        for extension in initial_extensions:
            self.bot.unload_extension(extension)
        try:
            for extension in initial_extensions:
                self.bot.load_extension(extension)
        except Exception:
            await ctx.send("An error occured while reloading: ```{}```".format(
                           traceback.format_exc()))
        await ctx.send(
            "Reloaded following extensions: {}".format(initial_extensions))


def setup(bot):
    bot.add_cog(Reload(bot))
