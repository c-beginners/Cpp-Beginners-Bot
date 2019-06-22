"""This module contains useful utility functions."""

import logging
import redis
import sys


def configure_logger(log_name=None, log_level=logging.DEBUG, log_file=None):
    """Configures a logger."""
    if log_name:
        logger = logging.getLogger(log_name)
    else:
        logger = logging.getLogger()

    # Set log level
    if isinstance(log_level, str):
        numeric_level = getattr(logging, log_level.upper(), None)
    elif isinstance(log_level, int):
        numeric_level = log_level
    else:
        raise ValueError('Invalid log level: %s' % log_level)
    logger.setLevel(numeric_level)

    # Set log file
    if log_file:
        handler = logging.FileHandler(filename=log_file, encoding='utf-8', mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
        logger.addHandler(handler)

    return logger


def get_redis_keys(redis_password):
    """Get a list of keys in the Redis database."""
    try:
        keys = redis.Redis(password=redis_password).keys()
    except redis.exceptions.ConnectionError:
        logging.critical('Could not connect to redis server')
        sys.exit(1)

    return list(map(lambda k: k.decode('utf-8'), keys))
