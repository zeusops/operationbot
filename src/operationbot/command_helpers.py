from typing import cast

from discord.channel import TextChannel
from discord.ext.commands import Context

from operationbot import messageFunctions as msgFnc
from operationbot.bot import OperationBot
from operationbot.errors import MessageNotFound
from operationbot.event import Event
from operationbot.eventDatabase import EventDatabase


async def update_event(
    event: Event, bot: OperationBot, import_db=False, reorder=True, export=True
) -> bool:
    """Update event message.

    Creates a new message if missing.

    Args:
        event (Event): Event to be updated
        bot (OperationBot): The main bot instance
        import_db (bool, optional): Import database during update.
                                    Defaults to False.
        reorder (bool, optional): Reorder message reactions to match event
                                    order (delete all and re-add).
                                    Defaults to True.
        export (bool, optional): Export database. Defaults to True.

    Returns:
        bool: Returns True if the message was edited.
    """
    # TODO: Move to a more appropriate location
    if import_db:
        await bot.import_database()
        # Event instance might have changed because of DB import, get again
        event = EventDatabase.getEventByMessage(event.messageID)

    changed = False
    try:
        message = await msgFnc.getEventMessage(event, bot)
    except MessageNotFound:
        message = await msgFnc.createEventMessage(event, bot.eventchannel)
        changed = True

    if await msgFnc.updateMessageEmbed(message, event):
        changed = True
    await msgFnc.updateReactions(event=event, message=message, reorder=reorder)
    if export:
        EventDatabase.toJson()
    return changed


async def show_event(ctx: Context, event: Event, bot: OperationBot):
    """Create a message for a single event

    Args:
        ctx (Context): Context to send the message to
        event (Event): Event to show
        bot (OperationBot): Main bot instance
    """
    message = await msgFnc.getEventMessage(event, bot)
    await ctx.send(f"<{message.jump_url}>")
    await msgFnc.createEventMessage(
        event, cast(TextChannel, ctx.channel), update_id=False
    )


async def set_dlc(ctx: Context, event: Event, bot: OperationBot, dlc: str = ""):
    """Set a DLC for an event

    Args:
        ctx (Context): Command context
        event (Event): Event to modify
        bot (OperationBot): Main bot instance
        dlc (str, optional): DLC to set. Defaults to "".
    """
    event.dlc = dlc
    await update_event(event, bot)
    if dlc:
        await ctx.send(f"DLC ```\n{event.dlc}\n``` set for operation {event}")
        await show_event(ctx, event, bot)
    else:
        await ctx.send(f"DLC cleared from operation {event}")
