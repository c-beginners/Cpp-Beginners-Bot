"""Admin extension."""

import logging

import discord
from discord.ext import commands

from cppbot.constants import ENABLED_EXTENSIONS


def setup(bot):
    """Set up extension."""
    bot.add_cog(AdminCog(bot))


class AdminCog(commands.Cog, name='Admin'):
    """Commands for channel administration."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command('load')
    @commands.has_permissions(administrator=True)
    async def load(self, ctx, *, module: str = None):
        """Load extensions."""
        try:
            self.bot.load_extension('cppbot.extensions.{0}'.format(module))
        except Exception as e:
            await ctx.send('{}: {}'.format(type(e).__name__, e))
        else:
            await ctx.send('Loaded extension!')

    @commands.command('unload')
    @commands.has_permissions(administrator=True)
    async def unload(self, ctx, *, module: str = None):
        """Unload extensions."""
        try:
            self.bot.unload_extension('cppbot.extensions.{0}'.format(module))
        except Exception as e:
            await ctx.send('{}: {}'.format(type(e).__name__, e))
        else:
            await ctx.send('Unloaded extension!')

    @commands.command('reload')
    @commands.has_permissions(administrator=True)
    async def reload(self, ctx, *, module: str = None):
        """Reload extensions."""
        for ext in ENABLED_EXTENSIONS:
            try:
                self.bot.reload_extension('cppbot.extensions.{0}'.format(ext))
            except Exception as e:
                await ctx.send('{}: {}'.format(type(e).__name__, e))
        await ctx.send('Reloaded extensions!')

    @commands.command('ban')
    @commands.has_permissions(ban_members=True)
    async def ban_user(self, ctx, member: discord.Member, reason=None, delete_message_days=1):
        """Ban a specified user."""
        try:
            await ctx.guild.ban(member, reason=reason, delete_message_days=delete_message_days)
        except discord.Forbidden:
            await ctx.send('This bot does not have the necessary permissions')
        except discord.HTTPException:
            await ctx.send('An unknown error occurred')

    @commands.command('purge')
    @commands.has_permissions(manage_messages=True)
    async def purge_user(self, ctx, member: discord.Member, channel: discord.TextChannel = None,
                         num_messages: int = None):
        """Purge the user's messages."""
        if not channel:
            channels = ctx.guild.text_channels
        else:
            channels = [ctx.channel]

        def is_user(message):
            return message.author.id == member.id

        for channel in channels:
            deleted = None

            try:
                deleted = await channel.purge(limit=num_messages + 1, check=is_user)
            except discord.Forbidden:
                await ctx.send('This bot does not have the necessary permissions')
            except discord.HTTPException:
                await ctx.send('An unknown error occurred')

            if deleted:
                logging.info('Deleted {0} message(s) from {1}'.format(len(deleted) - 1, channel))
