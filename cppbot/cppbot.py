"""This module contains the bot code for the Cpp Beginners Discord Bot."""

import argparse
import logging
import os
import sys

from discord.ext import commands
from leaderboard import leaderboard

from cppbot import utils
from cppbot.constants import DEFAULT_CONFIG_PATH, DEFAULT_CONFIG_SETTINGS
from cppbot.extensions import admin
from cppbot.utils import logger


class CppBot(commands.Bot):
    """Custom Discord client for the CppBot."""
    def __init__(self, redis_password):
        super().__init__('!')

        try:
            keys = utils.get_redis_keys(redis_password)
        except Exception as error:
            sys.exit(error)

        self.redis_password = redis_password
        self.lboards = {
            lboard: leaderboard.Leaderboard(lboard, page_size=10, password=redis_password)
            for lboard in keys
        }

    async def on_ready(self):
        """Logged on event."""
        logging.info('Logged on as %s', self.user)


def _main():
    # TODO - Remove this line
    utils.configure_logger(logging.DEBUG, logger)

    # Program args
    parser = argparse.ArgumentParser(description='Discord Bot for the Cpp Beginners channel.')
    parser.add_argument('--config', default=DEFAULT_CONFIG_PATH, help='specify a config file')
    args = parser.parse_args()

    # Configuration file
    config_path = args.config
    try:
        config = utils.read_config(config_path)
    except IOError:
        logger.warning('No config found... generating default config')
        config = utils.generate_config(config_path, DEFAULT_CONFIG_SETTINGS)
    logger.debug('Loaded config file')

    log_file = config['Debug Settings']['LOG_FILE']
    log_level = config['Debug Settings']['LOGGING_LEVEL']

    # Set logging settings
    utils.configure_logger(log_level, logger, log_file=log_file)
    utils.configure_logger(logging.WARNING, logging.getLogger('discord'))

    # Get secret keys from environment
    try:
        discord_key = os.environ['DISCORD_KEY']
    except KeyError:
        sys.exit('Cannot find discord key')
    try:
        redis_key = os.environ['REDIS_KEY']
    except KeyError:
        sys.exit('Cannot find redis key')

    # Start the discord client
    client = CppBot(redis_key)

    # Load bot extensions
    for ext in admin.ENABLED_EXTENSIONS:
        client.load_extension('cppbot.extensions.{0}'.format(ext))
    logger.debug('Loaded extensions')

    logger.info('Starting CppClient')
    client.run(discord_key)


if __name__ == '__main__':
    try:
        _main()
    except SystemExit as e:
        logger.critical(e)
        sys.exit(1)
