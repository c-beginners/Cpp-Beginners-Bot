"""This module contains useful utility functions."""

from configparser import ConfigParser
import logging

import redis

from cppbot.constants import DEFAULT_CONFIG_PATH, DEFAULT_LOG_FORMAT, DEFAULT_LOG_PATH

config = ConfigParser(allow_no_value=True, interpolation=None)
config.optionxform = str

log_handlers = []
logger = logging.getLogger(__name__)


def generate_config(config_path=DEFAULT_CONFIG_PATH, config_defaults=None):
    """Generate a default configuration."""
    if config_defaults:
        if not isinstance(config_defaults, list):
            raise ValueError('config_defaults must be a nested dict')

        for key, value in config_defaults:
            config[key] = value

    with open(config_path, 'w') as configfile:
        config.write(configfile)
    logger.debug('Generated config file at %s', config_path)

    return config


def read_config(config_path=DEFAULT_CONFIG_PATH):
    """Read a configuration file."""
    if not config.read(config_path):
        raise IOError('Config could not be loaded')
    logger.debug('Read config file from %s', config_path)

    return config


def configure_logger(log_level, logger, log_file=DEFAULT_LOG_PATH):
    """Configures a logger."""
    # Set log level
    if isinstance(log_level, str):
        numeric_level = getattr(logging, log_level.upper(), None)
    elif isinstance(log_level, int):
        numeric_level = log_level
    else:
        raise ValueError('Invalid log level: %s' % log_level)
    logger.setLevel(numeric_level)

    # Set log file
    if log_file and log_file not in log_handlers:
        handler = logging.FileHandler(filename=log_file, mode='a', encoding='utf-8')
        handler.setFormatter(DEFAULT_LOG_FORMAT)

        logger.addHandler(handler)
        log_handlers.append(log_file)

    return logger


def get_redis_keys(redis_password):
    """Get a list of keys in the Redis database."""
    keys = redis.Redis(password=redis_password).keys()

    key_list = list(map(bytes.decode, keys))

    return key_list
