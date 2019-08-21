"""The Admin extension."""

import logging

import discord
from discord.ext import commands

from cppbot.constants import ENABLED_EXTENSIONS

logger = logging.getLogger(__name__)


def setup(bot):
    """Add the Admin cog to the Discord bot."""
    bot.add_cog(AdminCog(bot))

    logger.info('Added Admin cog')


class AdminCog(commands.Cog, name='Admin'):
    """Commands for channel administration."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command('load')
    @commands.has_permissions(administrator=True)
    async def load(self, ctx, extension):
        """Load an extension.

        Args:
            extension (str): The extension to load.
        """
        try:
            self.bot.load_extension('cppbot.extensions.{0}'.format(extension))
        except Exception as e:
            await ctx.send('{}: {}'.format(type(e).__name__, e))
            logger.exception(str(e))
        else:
            await ctx.send('Loaded extension!')
            logger.info('Loaded extension!')

    @commands.command('unload')
    @commands.has_permissions(administrator=True)
    async def unload(self, ctx, extension):
        """Unload an extension.

        Args:
            extension (str): The extension to unload.
        """
        try:
            self.bot.unload_extension('cppbot.extensions.{0}'.format(extension))
        except Exception as e:
            await ctx.send('{}: {}'.format(type(e).__name__, e))
            logger.exception(str(e))
        else:
            await ctx.send('Unloaded extension!')
            logger.info('Unloaded extension!')

    @commands.command('reload')
    @commands.has_permissions(administrator=True)
    async def reload(self, ctx):
        """Reload all extensions."""
        for ext in ENABLED_EXTENSIONS:
            try:
                self.bot.reload_extension('cppbot.extensions.{0}'.format(ext))
            except Exception as e:
                await ctx.send('{}: {}'.format(type(e).__name__, e))
                logger.exception(str(e))

        await ctx.send('Reloaded extensions!')
        logger.info('Reloaded extensions!')

    @commands.command('ban')
    async def ban_user(self, ctx, member, reason=None, delete_message_days=1):
        """Ban a user.

        Args:
            member (str): A Discord username.
            reason (str, optional): The reason for the ban. Defaults to None.
            delete_message_days (int, optional): The number of days' worth of messages to delete. Defaults to 1.
        """
        try:
            await ctx.guild.ban(member, reason=reason, delete_message_days=delete_message_days)
        except discord.Forbidden as e:
            await ctx.send('This bot does not have the necessary permissions')
            logger.exception(str(e))
        except discord.HTTPException as e:
            await ctx.send('An unknown error occurred')
            logger.exception(str(e))

    @commands.command('purge')
    @commands.has_permissions(manage_messages=True)
    async def purge_user(self, ctx, member, channel=None, num_messages=None):
        """Purge a user's messages.

        Args:
            member (str): A Discord username.
            channel (str, optional): The channel to purge. Delete from all channels if not specified.
            num_messages (int, optional): The number of messages to purge. Deletes all messages if not specified.
        """
        def is_user(message):
            return message.author.id == member.id

        if not channel:
            channels = ctx.guild.text_channels
        else:
            channels = [ctx.channel]

        for channel in channels:
            deleted = None
            try:
                deleted = await channel.purge(limit=(num_messages + 1), check=is_user)
            except discord.Forbidden as e:
                await ctx.send('This bot does not have the necessary permissions')
                logger.exception(str(e))
            except discord.HTTPException as e:
                await ctx.send('An unknown error occurred')
                logger.exception(str(e))

            if deleted:
                logger.info('Deleted {0} message(s) from {1}'.format(len(deleted) - 1, channel))
