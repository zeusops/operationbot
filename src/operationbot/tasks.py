import asyncio

import operationbot.config as cfg
import operationbot.messageFunctions as msgFnc
from operationbot.bot import OperationBot


async def archive_past_events(bot: OperationBot):
    if not cfg.ARCHIVE_AUTOMATICALLY:
        return

    while True:
        await msgFnc.archive_past_events(bot, delta=cfg.ARCHIVE_AFTER_TIME)
        await asyncio.sleep(cfg.ARCHIVE_CHECK_DELAY)
