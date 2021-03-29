import discord
from discord import TextChannel, User
from discord.ext.commands import Bot, DefaultHelpCommand

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
                name = '{}|{}'.format(aliases[0], name)
            names[command.name] = name

        max_size = get_max_size(names)

        get_width = discord.utils._string_width
        for command in commands:
            name = names[command.name]
            width = max_size - (get_width(name) - len(name))
            entry = '{0}{1:<{width}} {2}'.format(
                self.indent * ' ', name, command.short_doc, width=width)
            self.paginator.add_line(self.shorten_text(entry))


class OperationBot(Bot):
    def __init__(self, *args, help_command=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.commandchannel: TextChannel
        self.logchannel: TextChannel
        self.eventchannel: TextChannel
        self.eventarchivechannel: TextChannel
        self.owner: User
        self.signoff_notify_user: User
        self.awaiting_reply = False

        if help_command is None:
            self.help_command = AliasHelpCommand()
        else:
            self.help_command = help_command

    def fetch_data(self) -> None:
        self.commandchannel = self.get_channel(cfg.COMMAND_CHANNEL)
        self.logchannel = self.get_channel(cfg.LOG_CHANNEL)
        self.eventchannel = self.get_channel(cfg.EVENT_CHANNEL)
        self.eventarchivechannel = self.get_channel(cfg.EVENT_ARCHIVE_CHANNEL)
        self.owner_id = ADMIN
        self.owner = self.get_user(self.owner_id)
        self.signoff_notify_user = self.get_user(SIGNOFF_NOTIFY_USER)

    async def import_database(self):
        try:
            EventDatabase.loadDatabase(self.commandchannel.guild.emojis)
        except ValueError as e:
            await self.commandchannel.send(e)
            await self.logout()
