import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from operationbot.bot import OperationBot
import operationbot.config as cfg
import operationbot.messageFunctions as msgFnc

# OperationBot: TypeAlias = operationbot.bot.OperationBot


async def archive_past_events(bot: "OperationBot"):
    if not cfg.ARCHIVE_AUTOMATICALLY:
        logging.info("Automatic archival disabled, skipping archive_past_events task")
        return

    logging.info("Started archive_past_events task")

    while True:
        await msgFnc.archive_past_events(bot, delta=cfg.ARCHIVE_AFTER_TIME)
        await asyncio.sleep(cfg.ARCHIVE_CHECK_DELAY)


async def cancel_empty_events(bot: "OperationBot"):
    if not cfg.CANCEL_AUTOMATICALLY:
        logging.info(
            "Automatic cancellation disabled, skipping cancel_empty_events task"
        )
        return

    logging.info("Started cancel_empty_events task")

    while True:
        try:
            await msgFnc.cancel_empty_events(bot, threshold=cfg.CANCEL_THRESHOLD)
        except Exception as e:
            logging.error(e)
        await asyncio.sleep(cfg.CANCEL_CHECK_DELAY)


ALL_TASKS = {
    "Archive past events": archive_past_events,
    "Cancel empty events": cancel_empty_events,
}
