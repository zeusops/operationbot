# Modified from https://github.com/Rapptz/RoboDanny/blob/master/cogs/repl.py

import inspect
import io
import textwrap
import traceback
from contextlib import redirect_stdout
from typing import Set

import discord
from discord.ext import commands
from discord.ext.commands import (BadArgument, Bot, Cog, Context,
                                  MissingRequiredArgument, command)

from eventDatabase import EventDatabase  # noqa
from secret import COMMAND_CHAR as CMD


class REPL(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self._last_result = None
        self.sessions: Set[int] = set()

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    def get_syntax_error(self, e):
        if e.text is None:
            return '```py\n{0.__class__.__name__}: {0}\n```'.format(e)
        return '```py\n{0.text}{1:>{0.offset}}\n{2}: {0}```'.format(
            e, '^', type(e).__name__)

    @commands.command(pass_context=True, hidden=True, name='eval')
    @commands.is_owner()
    async def _eval(self, ctx: Context, *, body: str):
        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.message.channel,
            'author': ctx.message.author,
            'guild': ctx.message.guild,
            'message': ctx.message,
            '_': self._last_result
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = 'async def func():\n%s' % textwrap.indent(body, '  ')

        try:
            exec(to_compile, env)
        except SyntaxError as e:
            return await ctx.send(self.get_syntax_error(e))

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception:
            value = stdout.getvalue()
            await ctx.send('```py\n{}{}\n```'.format(
                value, traceback.format_exc()))
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('\u2705')
            except Exception:
                await ctx.send('```py\n{}\n```'
                               .format(traceback.format_exc()))

            if ret is None:
                if value:
                    await ctx.send('```py\n%s\n```' % value)
            else:
                self._last_result = ret
                await ctx.send('```py\n%s%s\n```' % (value, ret))

    @commands.command(pass_context=True, hidden=True)
    @commands.is_owner()
    async def repl(self, ctx: Context):
        msg = ctx.message

        variables = {
            'ctx': ctx,
            'bot': self.bot,
            'message': msg,
            'guild': msg.guild,
            'channel': msg.channel,
            'author': msg.author,
            '_': None,
        }

        if msg.channel.id in self.sessions:
            await ctx.send(
                'Already running a REPL session in this channel.'
                'Exit it with `quit`.')
            return

        self.sessions.add(msg.channel.id)
        await ctx.send('Enter code to execute or evaluate.'
                       '`exit()` or `quit` to exit.')

        def pred(m):
            return m.author == msg.author and m.channel == msg.channel \
                and m.content.startswith('`')
        while True:
            response = await self.bot.wait_for(
                'message', check=pred)

            cleaned = self.cleanup_code(response.content)

            if cleaned in ('quit', 'exit', 'exit()'):
                await ctx.send('Exiting.')
                self.sessions.remove(msg.channel.id)
                return

            executor = exec
            if cleaned.count('\n') == 0:
                # single statement, potentially 'eval'
                try:
                    code = compile(cleaned, '<repl session>', 'eval')
                except SyntaxError:
                    pass
                else:
                    executor = eval

            if executor is exec:
                try:
                    code = compile(cleaned, '<repl session>', 'exec')
                except SyntaxError as e:
                    await ctx.send(self.get_syntax_error(e))
                    continue

            variables['message'] = response

            fmt = None
            stdout = io.StringIO()

            try:
                with redirect_stdout(stdout):
                    result = executor(code, variables)
                    if inspect.isawaitable(result):
                        result = await result
            except Exception:
                value = stdout.getvalue()
                fmt = '```py\n{}{}\n```'.format(value, traceback.format_exc())
            else:
                value = stdout.getvalue()
                if result is not None:
                    fmt = '```py\n{}{}\n```'.format(value, result)
                    variables['_'] = result
                elif value:
                    fmt = '```py\n{}\n```'.format(value)

            try:
                if fmt is not None:
                    if len(fmt) > 2000:
                        await ctx.send('Content too big to be printed.')
                        print(fmt)
                    else:
                        await ctx.send(fmt)
            except discord.Forbidden:
                pass
            except discord.HTTPException as e:
                await ctx.send('Unexpected error: `{}`'.format(e))

    @repl.error
    @_eval.error
    async def command_error(self, ctx: Context, error):
        if isinstance(error, MissingRequiredArgument):
            await ctx.send("Missing argument. See: {}help {}"
                           .format(CMD, ctx.command))
        elif isinstance(error, BadArgument):
            await ctx.send("Invalid argument: {}. See: {}help {}"
                           .format(error, CMD, ctx.command))
        else:
            await ctx.send("Unexpected error occured: ```{}```".format(error))
            print(error)


def setup(bot):
    bot.add_cog(REPL(bot))
