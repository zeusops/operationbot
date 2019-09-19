from discord.ext.commands import Bot

import config as cfg


class OperationBot(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.commandchannel      = self.get_channel(cfg.COMMAND_CHANNEL)
        self.log_channel         = self.get_channel(cfg.LOG_CHANNEL)
        self.eventchannel        = self.get_channel(cfg.EVENT_CHANNEL)
        self.eventarchivechannel = self.get_channel(cfg.EVENT_ARCHIVE_CHANNEL)
