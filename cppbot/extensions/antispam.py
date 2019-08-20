import logging

import antispam
import discord
from discord.ext import commands

from cppbot.constants import SPAM_THRESHOLD

logger = logging.getLogger(__name__)


def setup(bot):
    """Set up extension."""
    bot.add_cog(AntispamCog(bot))


def is_spam(message):
    """Checks if a given message is spam.

    Args:
        message (discord.Message): The message to check.

    Returns:
        bool: Indicates whether the message is spam.
    """
    try:
        spam_score = antispam.score(message.content)
        if spam_score >= SPAM_THRESHOLD:
            logger.info('Message from %s with spam score %s', message.author, spam_score)
            return True
        else:
            return False
    except TypeError:
        # Ignore input bug
        pass
    except discord.errors.Forbidden as err:
        logger.error(str(err))


class AntispamCog(commands.Cog, name='Admin'):
    """Commands for channel administration."""
    def __init__(self, bot):
        self.bot = bot

    async def on_message(self, message):
        logger.debug('Received message from %s', message.author)

        # TODO - Decide how to handle spam messages
        if is_spam(message):
            pass

        await self.process_commands(message)
