"""Admin extension."""

from discord.ext import commands

from cppbot.constants import ENABLED_EXTENSIONS


def setup(bot):
    """Set up extension."""
    bot.add_cog(AdminCog(bot))


class AdminCog(commands.Cog, name='Admin'):
    """Commands for channel administration."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command('load')
    @commands.has_permissions(administrator=True)
    async def load(self, ctx, *, module: str = None):
        """Load extensions."""
        try:
            self.bot.load_extension('cppbot.extensions.{0}'.format(module))
        except Exception as e:
            await ctx.send('{}: {}'.format(type(e).__name__, e))
        else:
            await ctx.send('Loaded extension!')

    @commands.command('unload')
    @commands.has_permissions(administrator=True)
    async def unload(self, ctx, *, module: str = None):
        """Unload extensions."""
        try:
            self.bot.unload_extension('cppbot.extensions.{0}'.format(module))
        except Exception as e:
            await ctx.send('{}: {}'.format(type(e).__name__, e))
        else:
            await ctx.send('Unloaded extension!')

    @commands.command('reload')
    @commands.has_permissions(administrator=True)
    async def reload(self, ctx, *, module: str = None):
        """Reload extensions."""
        for ext in ENABLED_EXTENSIONS:
            try:
                self.bot.reload_extension('cppbot.extensions.{0}'.format(ext))
            except Exception as e:
                await ctx.send('{}: {}'.format(type(e).__name__, e))
        await ctx.send('Reloaded extensions!')
