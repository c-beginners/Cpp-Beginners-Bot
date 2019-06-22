"""This module contains the bot code for the Cpp Beginners Discord Bot."""

import argparse
from configparser import ConfigParser
import logging
import os.path
import sys

import antispam
import discord.errors
from discord.ext import commands
from leaderboard import leaderboard

from cppbot import utils
from cppbot.extensions import admin

# Bot info
__version__ = '0.2.4'

# Defaults
DEFAULT_CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.ini'))
DEFAULT_LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'discord.log'))

# Antispam
SPAM_THRESHOLD = 0.90


class CppBot(commands.Bot):
    """Custom Discord client for the CppBot."""
    def __init__(self, redis_password):
        super().__init__('!', case_insensitive=True)

        self.redis_password = redis_password
        self.lboards = {
            lboard: leaderboard.Leaderboard(lboard, page_size=10, password=redis_password)
            for lboard in utils.get_redis_keys(redis_password)
        }

    async def on_ready(self):
        """Logged on event."""
        logging.info('Logged on as %s', self.user)

    async def on_message(self, message):
        """On message."""
        logging.debug('Received message')
        try:
            spam_score = antispam.score(message.content)
            if spam_score >= SPAM_THRESHOLD:
                await message.delete()
                logging.info('Deleted message from %s with spam score %s', message.author, spam_score)
        except TypeError:
            pass
        except discord.errors.Forbidden as err:
            logging.error(str(err))

        await self.process_commands(message)


def generate_config(config_path):
    """Generate the default CppBot configuration."""
    config = ConfigParser(allow_no_value=True, interpolation=None)
    config.optionxform = str

    config['API Settings'] = {}
    config['Debug Settings'] = {'LOG_FILE': DEFAULT_LOG_PATH,
                                'LOGGING_LEVEL': 'WARNING'}
    config['Leaderboard Settings'] = {}

    with open(config_path, 'w') as configfile:
        config.write(configfile)
    logging.debug('Generated config file at %s', config_path)

    return config


def read_config(config_path):
    """Read the CppBot configuration file."""
    config = ConfigParser(allow_no_value=True, interpolation=None)
    config.optionxform = str

    config.read(config_path)
    logging.debug('Read config file from %s', config_path)

    return config


def _main():
    utils.configure_logger(log_level=logging.DEBUG)

    # Program args
    parser = argparse.ArgumentParser(description='Discord Bot for the Cpp Beginners channel.')
    parser.add_argument('--config', default=DEFAULT_CONFIG_PATH, help='specify a config file')
    args = parser.parse_args()

    # Configuration file
    config_path = args.config
    if not os.path.exists(config_path):
        logging.warning('No config found... generating default config')
        config = generate_config(config_path)
    else:
        config = read_config(config_path)
    logging.debug('Loaded config file')

    log_file = config['Debug Settings']['LOG_FILE']
    log_level = config['Debug Settings']['LOGGING_LEVEL']

    # Set logging settings
    utils.configure_logger(None, log_level, log_file)

    # Get secret keys from environment
    try:
        discord_key = os.environ['DISCORD_KEY']
    except KeyError:
        logging.critical('Cannot find discord key')
        sys.exit(1)
    try:
        redis_key = os.environ['REDIS_KEY']
    except KeyError:
        logging.critical('Cannot find redis key')
        sys.exit(1)

    # Start the discord client
    client = CppBot(redis_key)

    # Load bot extensions
    for ext in admin.EXTENSIONS:
        client.load_extension('cppbot.extensions.{0}'.format(ext))
    logging.debug('Loaded extensions')

    logging.info('Starting CppClient')
    client.run(discord_key)


if __name__ == '__main__':
    _main()
