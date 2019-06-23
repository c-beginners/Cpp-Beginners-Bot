"""Admin extension."""

from discord.ext import commands

EXTENSIONS = ['admin', 'leaderboard']


def setup(bot):
    """Set up extension."""
    bot.add_cog(AdminCog(bot))


class AdminCog(commands.Cog, name='Admin'):
    """Commands for channel administration."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command('load', hidden=True)
    @commands.has_permissions(administrator=True)
    async def load(self, ctx, *, module: str = None):
        """Load extensions."""
        try:
            self.bot.load_extension(module)
        except Exception as e:
            await ctx.send('{}: {}'.format(type(e).__name__, e))
        else:
            await ctx.send('Loaded extension!')

    @commands.command('unload', hidden=True)
    @commands.has_permissions(administrator=True)
    async def unload(self, ctx, *, module: str = None):
        """Unload extensions."""
        try:
            self.bot.unload_extension(module)
        except Exception as e:
            await ctx.send('{}: {}'.format(type(e).__name__, e))
        else:
            await ctx.send('Unloaded extension!')

    @commands.command('reload', hidden=True)
    @commands.has_permissions(administrator=True)
    async def reload(self, ctx, *, module: str = None):
        """Reload extensions."""
        for ext in EXTENSIONS:
            try:
                self.bot.reload_extension('cppbot.extensions.{0}'.format(ext))
            except Exception as e:
                await ctx.send('{}: {}'.format(type(e).__name__, e))
        await ctx.send('Reloaded extensions!')
