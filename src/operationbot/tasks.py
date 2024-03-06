import asyncio
import logging

import operationbot.config as cfg
import operationbot.messageFunctions as msgFnc
from operationbot.bot import OperationBot


async def archive_past_events(bot: OperationBot):
    if not cfg.ARCHIVE_AUTOMATICALLY:
        logging.info("Automatic archival disabled, skipping archive_past_events task")
        return

    logging.info("Starting archive_past_events task")

    while True:
        await msgFnc.archive_past_events(bot, delta=cfg.ARCHIVE_AFTER_TIME)
        await asyncio.sleep(cfg.ARCHIVE_CHECK_DELAY)
