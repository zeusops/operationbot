from discord.ext.commands import Bot


class OperationBot(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
