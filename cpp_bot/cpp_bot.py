"""This module contains the bot logic for the Cpp Beginners Discord Bot."""

import argparse
import configparser
import logging
import os.path
import sys

import discord

# Bot info
__version__ = '0.1.0'
GITHUB_URL = 'https://github.com/c-beginners/CppBeginnersBot'

# Defaults
DEFAULT_CONFIG = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.ini'))
DEFAULT_LOG = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'discord.log'))

class CppClient(discord.Client):
    """Custom Discord client for the CppBot."""


def generate_config(config_path):
    """Generate the default CppBot configuration."""
    config = configparser.ConfigParser(allow_no_value=True)
    config.optionxform = str

    config['API Settings'] = {'API_TOKEN': None}
    config['Debug Settings'] = {'LOG_FILE': DEFAULT_LOG,
                                'LOGGING_LEVEL': 'WARNING'}

    with open(config_path, 'w') as configfile:
        config.write(configfile)
    logging.debug('Generated config file at %s', config_path)


def read_config(config_path):
    """Read the CppBot configuration file."""
    config = configparser.ConfigParser(allow_no_value=True)
    config.optionxform = str

    config.read(config_path)
    logging.debug('Read config file from %s', config_path)

    return config


def _configure_logger(log_file, log_level):
    """Set the default logger level."""
    logger = logging.getLogger()

    # Set log file
    if log_file:
        handler = logging.FileHandler(filename=log_file, encoding='utf-8', mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
        logger.addHandler(handler)

    # Set log level
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % log_level)
    logger.setLevel(numeric_level)


def _main():
    parser = argparse.ArgumentParser(description='Discord Bot for the Cpp Beginners channel.')
    parser.add_argument('--config', default=DEFAULT_CONFIG, help='specify a config file')

    args = parser.parse_args()

    # Read the bot config file
    if os.path.exists(args.config):
        config = read_config(args.config)

        api_key = config['API Settings']['API_TOKEN']
        log_file = config['Debug Settings']['LOG_FILE']
        log_level = config['Debug Settings']['LOGGING_LEVEL']

        logging.info('Read config file')
    else:
        generate_config(args.config)
        logging.warning('No config found... generating default config')
        sys.exit()

    _configure_logger(log_file, log_level)

    # Start the discord client
    client = CppClient()
    if api_key:
        logging.info('Starting CppClient')
        client.run(api_key)
    else:
        logging.error('No API key specified')
        sys.exit(1)


if __name__ == '__main__':
    _main()
