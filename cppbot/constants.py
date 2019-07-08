import logging
import os.path

# Logging
DEFAULT_LOG_NAME = 'cppbot'
DEFAULT_LOG_FORMAT = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
DEFAULT_LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'discord.log'))

# Config
DEFAULT_CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.ini'))
DEFAULT_CONFIG_SETTINGS = {
    'API Settings': {},
    'Debug Settings': {
        'LOG_FILE': DEFAULT_LOG_PATH,
        'LOGGING_LEVEL': 'WARNING'
        },
    'Leaderboard Settings': {}
}

# Admin
ENABLED_EXTENSIONS = ['admin', 'leaderboard']

# Antispam
SPAM_THRESHOLD = 0.90
