import traceback

from discord.ext.commands import Bot, Cog, Context, ExtensionNotLoaded, command

from main import initial_extensions


class Reload(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @command()
    async def reload(self, ctx: Context):
        print("Reloading extensions")
        unloaded = []
        for extension in initial_extensions:
            try:
                self.bot.unload_extension(extension)
                print("unloaded", extension)
            except ExtensionNotLoaded:
                await ctx.send("Skipping unload for not loaded extension {}"
                               .format(extension))
            else:
                unloaded.append(extension)
        loaded = []
        for extension in initial_extensions:
            try:
                self.bot.load_extension(extension)
                print("loaded", extension)
            except Exception:
                await ctx.send("An error occured while reloading: ```py\n{}```"
                               .format(traceback.format_exc()))
            else:
                loaded.append(extension)
        if len(loaded) > 0:
            await ctx.send(
                "Reloaded following extensions: {}".format(loaded))
            not_loaded = [item for item in unloaded if item not in loaded]
            if len(not_loaded) > 0:
                await ctx.send("Failed to reload following extensions: {}"
                               .format(not_loaded))


def setup(bot):
    bot.add_cog(Reload(bot))
