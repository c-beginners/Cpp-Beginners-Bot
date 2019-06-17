"""This module contains the bot logic for the Cpp Beginners Discord Bot."""

import argparse
from configparser import ConfigParser
import logging
import os.path
import sys

import discord.ext.commands
from leaderboard.leaderboard import Leaderboard
import redis
from texttable import Texttable

# Bot info
__version__ = '0.1.0'
GITHUB_URL = 'https://github.com/c-beginners/CppBeginnersBot'

# Defaults
DEFAULT_CONFIG = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.ini'))
DEFAULT_LOG = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'discord.log'))

class Points(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot

class Tasks(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot

class Users(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot

class CppBot(discord.ext.commands.Bot):
    """Custom Discord client for the CppBot."""
    def __init__(self, redis_key):
        super().__init__('!', case_insensitive=True)
        self.redis_client = redis.Redis(password=redis_key)
        self.lboards = {lboard_name: Leaderboard(lboard_name, page_size=10, password=redis_key)
                        for lboard_name
                        in map(lambda k: k.decode('utf-8'), self.redis_client.keys())}

    async def on_ready(self):
        """Logged on event."""
        print('Logged on as {0}!'.format(self.user))


def generate_config(config_path):
    """Generate the default CppBot configuration."""
    config = ConfigParser(allow_no_value=True, interpolation=None)
    config.optionxform = str

    config['API Settings'] = {'API_TOKEN': ''}
    config['Debug Settings'] = {'LOG_FILE': DEFAULT_LOG,
                                'LOGGING_LEVEL': 'WARNING'}
    config['Leaderboard Settings'] = {'REDIS_KEY': ''}

    with open(config_path, 'w') as configfile:
        config.write(configfile)
    logging.debug('Generated config file at %s', config_path)


def read_config(config_path):
    """Read the CppBot configuration file."""
    config = ConfigParser(allow_no_value=True, interpolation=None)
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


def leaderboard_list(lboard, page):
    """Create list from leaderboard."""
    lboard_list = [['rank', 'member', 'score']]
    for row in lboard.leaders(page):
        lboard_list.append([row['rank'], row['member'].decode('utf-8'), row['score']])
    return lboard_list


def _get_lboard_table(lboard, page):
    """Get the leaderboard as a text table."""
    table = Texttable()
    table.set_cols_align(['c', 'c', 'c'])
    table.set_cols_valign(['m', 'm', 'm'])

    table.add_rows(leaderboard_list(lboard, page))

    return table.draw()


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
        redis_key = config['Leaderboard Settings']['REDIS_KEY']

        logging.info('Read config file')
    else:
        generate_config(args.config)
        logging.warning('No config found... generating default config')
        sys.exit()

    _configure_logger(log_file, log_level)

    # Start the discord client
    client = CppBot(redis_key)

    # Commands
    @client.command('addtask')
    async def add_task(ctx, task, points=100):
        """Add a new task."""
        if ctx.message.author == client.user:
            return

        points = float(points)

        if task in client.lboards.keys():
            await ctx.message.channel.send('Task already exists!')
            return

        client.lboards[task] = Leaderboard(task, page_size=10, password=redis_key)

        logging.info('Added the task "%s" with %f points', task, points)


    @client.command('deltask')
    async def del_task(ctx, task):
        """Removes a task."""
        if ctx.message.author == client.user:
            return

        if task not in client.lboards.keys():
            await ctx.message.channel.send('Task doesn\'t exist!')
            return

        client.lboards[task].delete_leaderboard()
        client.lboards.pop(task)

        logging.info('Removed the task "%s"', task)


    @client.command('addpoints')
    async def add_points(ctx, user, task, points):
        """Add points to a user's task score."""
        if ctx.message.author == client.user:
            return

        points = float(points)

        if task not in client.lboards.keys():
            await ctx.message.channel.send('Task doesn\'t exist!')
            return
        if points < 0:
            await ctx.message.channel.send('Points should be greater than 0!')
            return

        current_points = client.lboards[task].score_for(user)
        if current_points:
            points += current_points
        client.lboards[task].rank_member(user, points)

        logging.info('Gave the user "%s" %f points', user, points)


    @client.command('delpoints')
    async def del_points(ctx, user, task, points):
        """Remove points from a user's task score."""
        if ctx.message.author == client.user:
            return

        points = float(points)

        if task not in client.lboards.keys():
            await ctx.message.channel.send('Task doesn\'t exist!')
            return
        if not client.lboards[task].check_member(user):
            await ctx.message.channel.send('User doesn\'t exist in the task!')
            return
        if points < 0:
            await ctx.message.channel.send('Points should be greater than 0!')
            return

        current_points = client.lboards[task].score_for(user)
        if current_points:
            points -= current_points
        client.lboards[task].rank_member(user, points)

        logging.info('Docked the user "%s" -%f points', user, points)


    @client.command('setpoints')
    async def set_points(ctx, user, task, points):
        """Set a user's task score."""
        if ctx.message.author == client.user:
            return

        points = float(points)

        if task not in client.lboards.keys():
            await ctx.message.channel.send('Task doesn\'t exist!')
            return

        client.lboards[task].rank_member(user, points)

        logging.info('Set the user "%s" to %f points', user, points)


    @client.command('adduser')
    async def add_user(ctx, user, task):
        """Add a user entry to a task."""
        if ctx.message.author == client.user:
            return

        if task not in client.lboards.keys():
            await ctx.message.channel.send('Task doesn\'t exist!')
            return
        if client.lboards[task].check_member(user):
            await ctx.message.channel.send('User already exists in the task!')
            return

        client.lboards[task].rank_member(user, 0)

        logging.info('Added the user "%s" to task %s', user, task)


    @client.command('deluser')
    async def del_user(ctx, user, task):
        """Removes a user entry from a task."""
        if ctx.message.author == client.user:
            return

        if task not in client.lboards.keys():
            await ctx.message.channel.send('Task doesn\'t exist!')
            return
        if not client.lboards[task].check_member(user):
            await ctx.message.channel.send('User doesn\'t exist in the task!')
            return

        client.lboards[task].remove_member(user)

        logging.info('Removed the user "%s" from task %s', user, task)


    @client.command('leaderboard')
    async def show_leaderboard(ctx, lboard_name, lboard_page=1):
        """Display the specified leaderboard."""
        if ctx.message.author == client.user:
            return

        if lboard_name not in client.lboards.keys():
            await ctx.message.channel.send('Leaderboard does not exist!')
            return
        if not client.lboards[lboard_name].total_members():
            await ctx.message.channel.send('Cannot display empty leaderboard!')
            return
        if lboard_page < 1 or client.lboards[lboard_name].total_pages() < lboard_page:
            await ctx.message.channel.send('Invalid page number!')
            return

        leaderboard_msg = '```' \
                          + 'Leaderboard "' + lboard_name + '"\n\n' + \
                          _get_lboard_table(client.lboards[lboard_name],
                                            lboard_page) \
                          + '\n\n**Page ' + str(lboard_page) + '**' \
                          + '```'
        await ctx.message.channel.send(leaderboard_msg)

        logging.info('Displayed leaderboard "%s" page %d', lboard_name, lboard_page)

    if api_key:
        logging.info('Starting CppClient')
        client.run(api_key)
    else:
        logging.error('No API key specified')
        sys.exit(1)


if __name__ == '__main__':
    _main()
