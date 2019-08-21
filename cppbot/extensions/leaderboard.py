"""The Leaderboard extension."""

import logging

from discord.ext import commands
from leaderboard.leaderboard import Leaderboard
from texttable import Texttable

logger = logging.getLogger(__name__)


def setup(bot):
    """Add the Leaderboard cog to the Discord bot."""
    bot.add_cog(LeaderboardCog(bot))

    logger.info('Added Leaderboard cog')


def leaderboard_list(lboard, page):
    """Get a leaderboard page as a list.

    Args:
        lboard (leaderboard.leaderboard.Leaderboard): The leaderboard.
        page (int): The leaderboard page.

    Returns:
        list: A 2D list representation of the leaderboard.
    """
    lboard_list = [
        ['rank', 'member', 'score']
    ]

    # Append rows to leaderboard list
    for row in lboard.leaders(page):
        lboard_list.append([row['rank'], row['member'].decode('utf-8'), row['score']])

    return lboard_list


def get_lboard_text(lboard, page):
    """Get a leaderboard page as a text table.

    Args:
        lboard (leaderboard.leaderboard.Leaderboard): The leaderboard.
        page (int): The leaderboard page.

    Returns:
        str: The leaderboard as a text table.
    """
    table = Texttable()

    # Set text alignment
    table.set_cols_align(['c', 'c', 'c'])
    table.set_cols_valign(['m', 'm', 'm'])

    # Import the leaderboard into the table
    table.add_rows(leaderboard_list(lboard, page))

    return table.draw()


class LeaderboardCog(commands.Cog, name='Leaderboard'):
    """Commands for the leaderboards."""
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def leaderboard(self, ctx):
        """The leaderboard command group."""
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid leaderboard command passed...')

    @leaderboard.group()
    async def user(self, ctx):
        """The leaderboard user subcommand."""
        if ctx.invoked_subcommand is self.user:
            await ctx.send('Invalid user command passed...')

    # TODO - Implement point limiting
    @leaderboard.command('add')
    async def add_leaderboard(self, ctx, leaderboard, points=100):
        """Add a leaderboard.

        Args:
            leaderboard (str): The leaderboard name.
            points (int, optional): The max number of points available. Defaults to 100.
        """
        if leaderboard in self.bot.lboards.keys():
            await ctx.send('Leaderboard already exists!')
            return

        self.bot.lboards[leaderboard] = Leaderboard(leaderboard, page_size=10, password=self.bot.redis_key)

        logger.info('Added the leaderboard "%s" with %f points', leaderboard, points)

    @leaderboard.command('remove')
    async def remove_leaderboard(self, ctx, leaderboard):
        """Remove a leaderboard.

        Args:
            leaderboard (str): The leaderboard name.
        """
        if leaderboard not in self.bot.lboards.keys():
            await ctx.send('Leaderboard does not exist!')
            return

        self.bot.lboards[leaderboard].delete_leaderboard()
        self.bot.lboards.pop(leaderboard)

        logger.info('Removed the leaderboard "%s"', leaderboard)

    @leaderboard.command('show')
    async def show_leaderboard(self, ctx, leaderboard, page=1):
        """Show the specified leaderboard.

        Args:
            leaderboard (str): The leaderboard name.
            page (int, optional): The leaderboard page to display. Defaults to 1.
        """
        if leaderboard not in self.bot.lboards.keys():
            await ctx.send('Leaderboard does not exist!')
            return
        elif not self.bot.lboards[leaderboard].total_members():
            await ctx.send('Cannot display empty leaderboard!')
            return
        elif page < 1 or self.bot.lboards[leaderboard].total_pages() < page:
            await ctx.send('Invalid page number')
            return

        leaderboard_msg = '```' \
                          + 'Leaderboard "' + leaderboard + '"\n\n' + \
                          get_lboard_text(self.bot.lboards[leaderboard], page) \
                          + '\n\n**Page ' + str(page) + '**' \
                          + '```'
        await ctx.send(leaderboard_msg)

        logger.info('Displayed leaderboard "%s" page %d', leaderboard, page)

    @leaderboard.command('list')
    async def list_leaderboards(self, ctx):
        """List all leaderboards."""
        lboard_list = '\n'.join(self.bot.lboards.keys())

        await ctx.send('```\n{0}\n```'.format(lboard_list))

    @user.command('add')
    async def add_user(self, ctx, user, leaderboard):
        """Add a user to a leaderboard.

        Args:
            user (str): A Discord username.
            leaderboard (str): The leaderboard name.
        """
        if leaderboard not in self.bot.lboards.keys():
            await ctx.send('Leaderboard does not exist!')
            return
        elif self.bot.lboards[leaderboard].check_member(user):
            await ctx.send('User is already on the leaderboard!')
            return

        self.bot.lboards[leaderboard].rank_member(user, 0)

        logger.info('Added the user "%s" to leaderboard "%s"', user, leaderboard)

    @user.command('remove')
    async def remove_user(self, ctx, user, leaderboard):
        """Remove a user from a leaderboard.

        Args:
            user (str): A Discord username.
            leaderboard (str): The leaderboard name.
        """
        if leaderboard not in self.bot.lboards.keys():
            await ctx.send('Leaderboard does not exist!')
            return
        elif not self.bot.lboards[leaderboard].check_member(user):
            await ctx.send('User is not on the leaderboard!')
            return

        self.bot.lboards[leaderboard].remove_member(user)

        logger.info('Removed the user "%s" from leaderboard "%s"', user, leaderboard)

    # TODO - Test what if user points is not set
    @user.command('give')
    async def give_points(self, ctx, user, leaderboard, points):
        """Give points to a user.

        Args:
            user (str): A Discord username.
            leaderboard (str): The leaderboard name.
            points (int or float): The number of points to give.
        """
        if leaderboard not in self.bot.lboards.keys():
            await ctx.send('Leaderboard does not exist!')
            return
        elif not self.bot.lboards[leaderboard].check_member(user):
            await ctx.send('User is not on the leaderboard!')
            return
        elif points < 0:
            await ctx.send('Points should be greater than 0!')
            return

        current_points = self.bot.lboards[leaderboard].score_for(user)
        if current_points:
            points += current_points

        self.bot.lboards[leaderboard].rank_member(user, points)

        logger.info('Gave the user "%s" %f points', user, points)

    # TODO - Test what if user points is not set
    @user.command('take')
    async def take_points(self, ctx, user, leaderboard, points):
        """Take points from a user.

        Args:
            user (str): A Discord username.
            leaderboard (str): The leaderboard name.
            points (int or float): The number of points to take.
        """
        if leaderboard not in self.bot.lboards.keys():
            await ctx.send('Leaderboard does not exist!')
            return
        elif not self.bot.lboards[leaderboard].check_member(user):
            await ctx.send('User is not on the leaderboard!')
            return
        elif points < 0:
            await ctx.send('Points should be greater than 0!')
            return

        current_points = self.bot.lboards[leaderboard].score_for(user)
        if current_points:
            points -= current_points

        self.bot.lboards[leaderboard].rank_member(user, points)

        logger.info('Docked the user "%s" -%f points', user, points)

    @user.command('set')
    async def set_points(self, ctx, user, leaderboard, points):
        """Set a user's points.

        Args:
            user (str): A Discord username.
            leaderboard (str): The leaderboard name.
            points (int or float): The user's new number of points.
        """
        if leaderboard not in self.bot.lboards.keys():
            await ctx.send('Leaderboard does not exist!')
            return
        elif not self.bot.lboards[leaderboard].check_member(user):
            await ctx.send('User is not on the leaderboard!')
            return

        self.bot.lboards[leaderboard].rank_member(user, points)

        logger.info('Set the user "%s" to %f points', user, points)
