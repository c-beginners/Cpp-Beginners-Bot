"""This module contains the bot logic for the Cpp Beginners Discord Bot."""

import argparse
from configparser import ConfigParser
import logging
import os.path
import sys

from discord.ext import commands
from leaderboard import leaderboard
import redis
from texttable import Texttable

# Bot info
__version__ = '0.2.0'

# Defaults
DEFAULT_CONFIG = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.ini'))
DEFAULT_LOG = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'discord.log'))

class AdminCog(commands.Cog, name='Admin'):
    """Commands for channel administration."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command('ban')
    async def ban_user(self, ctx, user):
        """Ban a specified user."""

    @commands.command('purge')
    async def purge_user(self, ctx, user):
        """Purge the user's messages."""


class LeaderboardCog(commands.Cog, name='Leaderboard'):
    """Commands for the task leaderboards."""
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def leaderboard_list(lboard, page):
        """Create list from leaderboard."""
        lboard_list = [['rank', 'member', 'score']]
        for row in lboard.leaders(page):
            lboard_list.append([row['rank'], row['member'].decode('utf-8'), row['score']])
        return lboard_list

    @staticmethod
    def _get_lboard_table(lboard, page):
        """Get the leaderboard as a text table."""
        table = Texttable()
        table.set_cols_align(['c', 'c', 'c'])
        table.set_cols_valign(['m', 'm', 'm'])

        table.add_rows(LeaderboardCog.leaderboard_list(lboard, page))

        return table.draw()

    @commands.command('addtask')
    async def add_task(self, ctx, task, points=100):
        """Add a new task."""
        if ctx.message.author == self.bot.user:
            return

        points = float(points)

        if task in self.bot.lboards.keys():
            await ctx.message.channel.send('Task already exists!')
            return

        self.bot.lboards[task] = leaderboard.Leaderboard(task, page_size=10,
                                                         password=self.bot.redis_key)

        logging.info('Added the task "%s" with %f points', task, points)

    @commands.command('deltask')
    async def del_task(self, ctx, task):
        """Removes a task."""
        if ctx.message.author == self.bot.user:
            return

        if task not in self.bot.lboards.keys():
            await ctx.message.channel.send('Task doesn\'t exist!')
            return

        self.bot.lboards[task].delete_leaderboard()
        self.bot.lboards.pop(task)

        logging.info('Removed the task "%s"', task)

    @commands.command('addpoints')
    async def add_points(self, ctx, user, task, points):
        """Add points to a user's task score."""
        if ctx.message.author == self.bot.user:
            return

        points = float(points)

        if task not in self.bot.lboards.keys():
            await ctx.message.channel.send('Task doesn\'t exist!')
            return
        if points < 0:
            await ctx.message.channel.send('Points should be greater than 0!')
            return

        current_points = self.bot.lboards[task].score_for(user)
        if current_points:
            points += current_points
        self.bot.lboards[task].rank_member(user, points)

        logging.info('Gave the user "%s" %f points', user, points)

    @commands.command('delpoints')
    async def del_points(self, ctx, user, task, points):
        """Remove points from a user's task score."""
        if ctx.message.author == self.bot.user:
            return

        points = float(points)

        if task not in self.bot.lboards.keys():
            await ctx.message.channel.send('Task doesn\'t exist!')
            return
        if not self.bot.lboards[task].check_member(user):
            await ctx.message.channel.send('User doesn\'t exist in the task!')
            return
        if points < 0:
            await ctx.message.channel.send('Points should be greater than 0!')
            return

        current_points = self.bot.lboards[task].score_for(user)
        if current_points:
            points -= current_points
        self.bot.lboards[task].rank_member(user, points)

        logging.info('Docked the user "%s" -%f points', user, points)

    @commands.command('setpoints')
    async def set_points(self, ctx, user, task, points):
        """Set a user's task score."""
        if ctx.message.author == self.bot.user:
            return

        points = float(points)

        if task not in self.bot.lboards.keys():
            await ctx.message.channel.send('Task doesn\'t exist!')
            return

        self.bot.lboards[task].rank_member(user, points)

        logging.info('Set the user "%s" to %f points', user, points)

    @commands.command('addentry')
    async def add_entry(self, ctx, user, task):
        """Add a user entry to a task."""
        if ctx.message.author == self.bot.user:
            return

        if task not in self.bot.lboards.keys():
            await ctx.message.channel.send('Task doesn\'t exist!')
            return
        if self.bot.lboards[task].check_member(user):
            await ctx.message.channel.send('User already exists in the task!')
            return

        self.bot.lboards[task].rank_member(user, 0)

        logging.info('Added the user entry "%s" to task %s', user, task)

    @commands.command('delentry')
    async def del_entry(self, ctx, user, task):
        """Removes a user entry from a task."""
        if ctx.message.author == self.bot.user:
            return

        if task not in self.bot.lboards.keys():
            await ctx.message.channel.send('Task doesn\'t exist!')
            return
        if not self.bot.lboards[task].check_member(user):
            await ctx.message.channel.send('User doesn\'t exist in the task!')
            return

        self.bot.lboards[task].remove_member(user)

        logging.info('Removed the user entry "%s" from task %s', user, task)

    @commands.command('leaderboard')
    async def show_leaderboard(self, ctx, lboard_name, lboard_page=1):
        """Display the specified leaderboard."""
        if ctx.message.author == self.bot.user:
            return

        if lboard_name not in self.bot.lboards.keys():
            await ctx.message.channel.send('Leaderboard does not exist!')
            return
        if not self.bot.lboards[lboard_name].total_members():
            await ctx.message.channel.send('Cannot display empty leaderboard!')
            return
        if lboard_page < 1 or self.bot.lboards[lboard_name].total_pages() < lboard_page:
            await ctx.message.channel.send('Invalid page number!')
            return

        leaderboard_msg = '```' \
                          + 'Leaderboard "' + lboard_name + '"\n\n' + \
                          LeaderboardCog._get_lboard_table(self.bot.lboards[lboard_name],
                                                           lboard_page) \
                          + '\n\n**Page ' + str(lboard_page) + '**' \
                          + '```'
        await ctx.message.channel.send(leaderboard_msg)

        logging.info('Displayed leaderboard "%s" page %d', lboard_name, lboard_page)

    @commands.command('leaderboards')
    async def list_leaderboards(self, ctx):
        """List all leaderboard names."""
        if ctx.message.author == self.bot.user:
            return

        lboard_list = ''
        for lboard_name in self.bot.lboards.keys():
            lboard_list += lboard_name + '\n'

        await ctx.message.channel.send(lboard_list)


class CppBot(commands.Bot):
    """Custom Discord client for the CppBot."""
    def __init__(self, redis_key):
        super().__init__('!', case_insensitive=True)
        self.redis_key = redis_key
        self.lboards = {lboard: leaderboard.Leaderboard(lboard, page_size=10,
                                                        password=redis_key)
                        for lboard in map(lambda k: k.decode('utf-8'),
                                          redis.Redis(password=redis_key).keys())}

    async def on_ready(self):
        """Logged on event."""
        logging.info('Logged on as %s!', self.user)


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

    client.add_cog(AdminCog(client))
    client.add_cog(LeaderboardCog(client))

    if api_key:
        logging.info('Starting CppClient')
        client.run(api_key)
    else:
        logging.error('No API key specified')
        sys.exit(1)


if __name__ == '__main__':
    _main()
