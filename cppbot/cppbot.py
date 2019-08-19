"""This module contains the bot code for the C++ Beginners Discord Bot."""

import argparse
import logging
import os

from discord.ext import commands
from leaderboard.leaderboard import Leaderboard

from cppbot import utils
from cppbot.constants import DEFAULT_CONFIG_PATH, DEFAULT_CONFIG_SETTINGS
from cppbot.extensions import admin
from cppbot.utils import logger


class CppBot(commands.Bot):
    """Custom Discord client for the CppBot."""
    def __init__(self, redis_password):
        # Prefix commands with character
        super().__init__('!')

        self.redis_password = redis_password

        # Initialize leaderboards
        self.lboards = {}
        for lboard in utils.get_redis_keys(redis_password):
            self.lboards[lboard] = Leaderboard(lboard, page_size=10, password=redis_password)

    async def on_ready(self):
        """Logged on event."""
        logger.info('Logged on as %s', self.user)


def load_config(config_path):
    """Loads a config file."""
    try:
        config = utils.read_config(config_path)
    except IOError:
        logger.warning('No config found... generating default config')
        config = utils.generate_config(config_path, DEFAULT_CONFIG_SETTINGS)

    logger.info('Loaded config file')
    return config


def _main():
    # TODO - Remove this line
    utils.configure_logger(logging.DEBUG, logger)

    # Program args
    parser = argparse.ArgumentParser(description='Discord Bot for the Cpp Beginners channel.')
    parser.add_argument('--config', default=DEFAULT_CONFIG_PATH, help='specify a config file')
    args = parser.parse_args()

    config = load_config(args.config)

    log_file = config['Debug Settings']['LOG_FILE']
    log_level = config['Debug Settings']['LOGGING_LEVEL']

    # Set logging settings
    utils.configure_logger(log_level, logger, log_file=log_file)
    # Only show warnings from the discord logger
    utils.configure_logger(logging.WARNING, logging.getLogger('discord'))

    # Get secret keys from environment
    discord_key = os.environ['DISCORD_KEY']
    redis_key = os.environ['REDIS_KEY']

    # Start the discord client
    client = CppBot(redis_key)

    # Load bot extensions
    for ext in admin.ENABLED_EXTENSIONS:
        client.load_extension('cppbot.extensions.{0}'.format(ext))
    logger.debug('Loaded extensions')

    logger.info('Starting CppClient')
    client.run(discord_key)


if __name__ == '__main__':
    _main()
