# Modified from https://github.com/Rapptz/RoboDanny/blob/master/cogs/repl.py

import inspect
import io
import textwrap
import traceback
from contextlib import redirect_stdout
from typing import Set

import discord
from discord.ext import commands
from discord.ext.commands import (BadArgument, Bot, Context,
                                  MissingRequiredArgument)
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
            return f'```py\n{e.__class__.__name__}: {e}\n```'
        return f'```py\n{e.text}{"^":>{e.offset}}\n{type(e).__name__}: {e}```'

    @commands.command(name='eval', hidden=True)
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

        to_compile = f"async def func():\n{textwrap.indent(body, '  ')}"

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
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('\u2705')
            except Exception:
                await ctx.send(f'```py\n{traceback.format_exc()}\n```')

            if ret is None:
                if value:
                    await ctx.send(f'```py\n{value}\n```')
            else:
                self._last_result = ret
                await ctx.send(f'```py\n{value}{ret}\n```')

    @commands.command(hidden=True)
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
            'db': EventDatabase,
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
                fmt = f'```py\n{value}{traceback.format_exc()}\n```'
            else:
                value = stdout.getvalue()
                if result is not None:
                    fmt = f'```py\n{value}{result}\n```'
                    variables['_'] = result
                elif value:
                    fmt = f'```py\n{value}\n```'

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
                await ctx.send(f'Unexpected error: `{e}`')

    @repl.error
    @_eval.error
    async def command_error(self, ctx: Context, error):
        if isinstance(error, MissingRequiredArgument):
            await ctx.send(f"Missing argument. See: {CMD}help {ctx.command}")
        elif isinstance(error, BadArgument):
            await ctx.send(f"Invalid argument: {error}. See: {CMD}help "
                           f"{ctx.command}")
        else:
            await ctx.send(f"Unexpected error occured: ```{error}```")
            print(error)


def setup(bot):
    bot.add_cog(REPL(bot))
