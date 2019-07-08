import logging

import antispam
import discord
from discord.ext import commands

from cppbot.constants import SPAM_THRESHOLD


def setup(bot):
    """Set up extension."""
    bot.add_cog(AntispamCog(bot))


def is_spam(message):
    try:
        spam_score = antispam.score(message.content)
        if spam_score >= SPAM_THRESHOLD:
            logging.info('Message from %s with spam score %s', message.author, spam_score)
            return True
        else:
            return False
    except TypeError:
        pass
    except discord.errors.Forbidden as err:
        logging.error(str(err))


class AntispamCog(commands.Cog, name='Admin'):
    """Commands for channel administration."""
    def __init__(self, bot):
        self.bot = bot

    async def on_message(self, message):
        """On message."""
        logging.debug('Received message from %s', message.author)

        if is_spam(message):
            await message.delete()

        await self.process_commands(message)
