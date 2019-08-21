import logging

from cppbot.constants import DEFAULT_LOG_FORMAT

__version__ = '0.3.0'

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(DEFAULT_LOG_FORMAT)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(stream_handler)
