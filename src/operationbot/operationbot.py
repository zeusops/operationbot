"""A bot module that implements a custom help command and extra features."""

import logging
import sys
import traceback

import discord
from discord import TextChannel, User
from discord.ext.commands import Bot, DefaultHelpCommand
from discord.guild import Guild

import config as cfg
from eventDatabase import EventDatabase
from secret import ADMIN, SIGNOFF_NOTIFY_USER


class AliasHelpCommand(DefaultHelpCommand):
    """The implementation of a help command that displays command aliases."""

    def add_indented_commands(self, commands, *, heading, max_size=None):
        """Indents a list of commands after the specified heading.

        Copied with modifications from discord/ext/commands/help.py
        Includes the first alias of a command in the default help message.
        """

        # pylint: disable=W0212
        def get_max_size(names):
            as_lengths = (
                discord.utils._string_width(n)
                for n in names.values()
            )
            return max(as_lengths, default=0)

        if not commands:
            return

        self.paginator.add_line(heading)

        names = {}
        for command in commands:
            name = command.name
            aliases = command.aliases
            if aliases:
                name = f'{aliases[0]}|{name}'
            names[command.name] = name

        max_size = get_max_size(names)

        get_width = discord.utils._string_width
        for command in commands:
            name = names[command.name]
            width = max_size - (get_width(name) - len(name))
            entry = f'{self.indent * " "}{name:<{width}} {command.short_doc}'
            self.paginator.add_line(self.shorten_text(entry))


class OperationBot(Bot):
    """A custom Discord bot."""

    def __init__(self, *args, help_command=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.commandchannel: TextChannel
        self.logchannel: TextChannel
        self.eventchannel: TextChannel
        self.eventarchivechannel: TextChannel
        self.owner: User
        self.signoff_notify_user: User
        self.awaiting_reply = False
        self.processing = True

        if help_command is None:
            self.help_command = AliasHelpCommand()
        else:
            self.help_command = help_command

    def fetch_data(self) -> None:
        """Fetch channels and users from the Discord API after connecting."""
        self.commandchannel = self._get_channel(cfg.COMMAND_CHANNEL)
        self.logchannel = self._get_channel(cfg.LOG_CHANNEL)
        self.eventchannel = self._get_channel(cfg.EVENT_CHANNEL)
        self.eventarchivechannel = self._get_channel(cfg.EVENT_ARCHIVE_CHANNEL)
        self.owner_id = ADMIN
        self.owner = self._get_user(self.owner_id)
        self.signoff_notify_user = self._get_user(SIGNOFF_NOTIFY_USER)

    def _get_user(self, user_id: int) -> User:
        user = self.get_user(user_id)
        if user is None:
            raise TypeError(f"User ID {user_id} not found")
        return user

    def _get_channel(self, channel_id: int) -> TextChannel:
        channel = self.get_channel(channel_id)
        if channel is None:
            raise TypeError(f"Channel ID {channel_id} not found")
        if not isinstance(channel, TextChannel):
            raise TypeError(f"Channel ID {channel_id} is not a text channel")
        return channel

    def _get_guild(self, guild_id: int) -> Guild:
        guild = self.get_guild(guild_id)
        if guild is None:
            raise TypeError(f"Guild ID {guild_id} not found")
        return guild

    async def import_database(self) -> None:
        """Import the event database."""
        try:
            if cfg.EMOJI_GUILD:
                emoji_guild = self._get_guild(cfg.EMOJI_GUILD)
            else:
                emoji_guild = self.commandchannel.guild
            EventDatabase.loadDatabase(emoji_guild.emojis)
        except ValueError as e:
            await self.commandchannel.send(f"Error: {e}")
            logging.exception("Error loading database")
            await self.close()
            sys.exit()

    async def on_error(self, event_method, *args, **kwargs):
        print(f"Error in {event_method=}")
        traceback.print_exc()
        trace = traceback.format_exc(2)
        _, error, _ = sys.exc_info()

        ctx = self.commandchannel
        msg = (f"Unexpected error occured in {event_method}: ```{error}```\n"
               f"```py\n{trace}```")
        if len(msg) >= 2000:
            await ctx.send("Received error message that's over 2000 "
                           "characters, check log.")
            print(msg)
        else:
            await ctx.send(msg)
