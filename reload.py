import traceback

from discord.ext.commands import Bot, Cog, Context, ExtensionNotLoaded, command

from main import initial_extensions


class Reload(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @command()
    async def reload(self, ctx: Context):
        print("Reloading extensions")
        for extension in initial_extensions:
            try:
                self.bot.unload_extension(extension)
                print("unloaded", extension)
            except ExtensionNotLoaded:
                await ctx.send("Ignoring not loaded extension {}"
                               .format(extension))
        try:
            for extension in initial_extensions:
                self.bot.load_extension(extension)
                print("loaded", extension)
        except Exception:
            await ctx.send("An error occured while reloading: ```{}```"
                           .format(traceback.format_exc()))
        await ctx.send(
            "Reloaded following extensions: {}".format(initial_extensions))


def setup(bot):
    bot.add_cog(Reload(bot))
