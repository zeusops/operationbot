from discord import TextChannel, User
from discord.ext.commands import Bot

import config as cfg
from secret import ADMIN, SIGNOFF_NOTIFY_USER


class OperationBot(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commandchannel: TextChannel
        self.logchannel: TextChannel
        self.eventchannel: TextChannel
        self.eventarchivechannel: TextChannel
        self.owner: User
        self.signoff_notify_user: User
        self.awaiting_reply = False

    def fetch_data(self) -> None:
        self.commandchannel      = self.get_channel(cfg.COMMAND_CHANNEL)
        self.logchannel          = self.get_channel(cfg.LOG_CHANNEL)
        self.eventchannel        = self.get_channel(cfg.EVENT_CHANNEL)
        self.eventarchivechannel = self.get_channel(cfg.EVENT_ARCHIVE_CHANNEL)
        self.owner               = self.get_user(ADMIN)
        self.owner_id            = ADMIN
        self.signoff_notify_user = self.get_user(SIGNOFF_NOTIFY_USER)
