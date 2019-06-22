"""Leaderboard extension."""

import logging

from discord.ext import commands
from leaderboard.leaderboard import Leaderboard
from texttable import Texttable


def setup(bot):
    """Set up extension."""
    bot.add_cog(LeaderboardCog(bot))


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


class LeaderboardCog(commands.Cog, name='Leaderboard'):
    """Commands for the leaderboard leaderboards."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command('addlb')
    async def add_leaderboard(self, ctx, leaderboard, points=100):
        """Add a new leaderboard."""
        points = float(points)

        if leaderboard in self.bot.lboards.keys():
            await ctx.send('Leaderboard already exists!')
            return

        self.bot.lboards[leaderboard] = Leaderboard(leaderboard, page_size=10,
                                                    password=self.bot.redis_key)

        logging.info('Added the leaderboard "%s" with %f points', leaderboard, points)

    @commands.command('dellb')
    async def del_leaderboard(self, ctx, leaderboard):
        """Removes a leaderboard."""
        if leaderboard not in self.bot.lboards.keys():
            await ctx.send('Leaderboard doesn\'t exist!')
            return

        self.bot.lboards[leaderboard].delete_leaderboard()
        self.bot.lboards.pop(leaderboard)

        logging.info('Removed the leaderboard "%s"', leaderboard)

    @commands.command('addpoints')
    async def add_points(self, ctx, user, leaderboard, points):
        """Add points to a user's leaderboard score."""
        points = float(points)

        if leaderboard not in self.bot.lboards.keys():
            await ctx.send('Leaderboard doesn\'t exist!')
            return
        if points < 0:
            await ctx.send('Points should be greater than 0!')
            return

        current_points = self.bot.lboards[leaderboard].score_for(user)
        if current_points:
            points += current_points
        self.bot.lboards[leaderboard].rank_member(user, points)

        logging.info('Gave the user "%s" %f points', user, points)

    @commands.command('delpoints')
    async def del_points(self, ctx, user, leaderboard, points):
        """Remove points from a user's leaderboard score."""
        points = float(points)

        if leaderboard not in self.bot.lboards.keys():
            await ctx.send('Leaderboard doesn\'t exist!')
            return
        if not self.bot.lboards[leaderboard].check_member(user):
            await ctx.send('User doesn\'t exist in the leaderboard!')
            return
        if points < 0:
            await ctx.send('Points should be greater than 0!')
            return

        current_points = self.bot.lboards[leaderboard].score_for(user)
        if current_points:
            points -= current_points
        self.bot.lboards[leaderboard].rank_member(user, points)

        logging.info('Docked the user "%s" -%f points', user, points)

    @commands.command('setpoints')
    async def set_points(self, ctx, user, leaderboard, points):
        """Set a user's leaderboard score."""
        points = float(points)

        if leaderboard not in self.bot.lboards.keys():
            await ctx.send('Leaderboard doesn\'t exist!')
            return

        self.bot.lboards[leaderboard].rank_member(user, points)

        logging.info('Set the user "%s" to %f points', user, points)

    @commands.command('addentry')
    async def add_entry(self, ctx, user, leaderboard):
        """Add a user entry to a leaderboard."""
        if leaderboard not in self.bot.lboards.keys():
            await ctx.send('Leaderboard doesn\'t exist!')
            return
        if self.bot.lboards[leaderboard].check_member(user):
            await ctx.send('User already exists in the leaderboard!')
            return

        self.bot.lboards[leaderboard].rank_member(user, 0)

        logging.info('Added the user entry "%s" to leaderboard %s', user, leaderboard)

    @commands.command('delentry')
    async def del_entry(self, ctx, user, leaderboard):
        """Removes a user entry from a leaderboard."""
        if leaderboard not in self.bot.lboards.keys():
            await ctx.send('Leaderboard doesn\'t exist!')
            return
        if not self.bot.lboards[leaderboard].check_member(user):
            await ctx.send('User doesn\'t exist in the leaderboard!')
            return

        self.bot.lboards[leaderboard].remove_member(user)

        logging.info('Removed the user entry "%s" from leaderboard %s', user, leaderboard)

    @commands.command('lb')
    async def show_leaderboard(self, ctx, lboard_name, lboard_page=1):
        """Display the specified leaderboard."""
        if lboard_name not in self.bot.lboards.keys():
            await ctx.send('Leaderboard does not exist!')
            return
        if not self.bot.lboards[lboard_name].total_members():
            await ctx.send('Cannot display empty leaderboard!')
            return
        if lboard_page < 1 or self.bot.lboards[lboard_name].total_pages() < lboard_page:
            await ctx.send('Invalid page number')
            return

        leaderboard_msg = '```' \
                          + 'Leaderboard "' + lboard_name + '"\n\n' + \
                          _get_lboard_table(self.bot.lboards[lboard_name],
                                            lboard_page) \
                          + '\n\n**Page ' + str(lboard_page) + '**' \
                          + '```'
        await ctx.send(leaderboard_msg)

        logging.info('Displayed leaderboard "%s" page %d', lboard_name, lboard_page)

    @commands.command('listlbs')
    async def list_leaderboards(self, ctx):
        """List all leaderboard names."""
        lboard_list = '\n'.join(self.bot.lboards.keys())

        await ctx.send('```\n{0}\n```'.format(lboard_list))
