import discord
from discord.ext import commands
from menu import ConfigurationMenu

class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.hybrid_command()
    async def config(self, ctx):
        """
        Configure the bot.
        """
        
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You need to have the administrator permission to run this command.",
                    color=0x2F3136
                )
            )
        
        sett = await self.bot.settings.find_one({"_id": ctx.guild.id}) or {
            "_id": ctx.guild.id
        }
        
        embed = discord.Embed(
            title="Automatic ER:LC Discord Checker Configuration",
            description="To configure the bot, please provide the following information.",
            color=0x2F3136
        ).add_field(
            name="Alert Channel",
            value="Please mention the channel where alerts will be sent."
        ).add_field(
            name="API Key",
            value=f"{"_Added_" if sett.get("api_key") else "Please provide the API key."}"
        ).add_field(
            name="Message",
            value=f"{"No Custom Message" if not sett.get("message") else sett['message']}"
        )

        view = ConfigurationMenu(self.bot, sett, ctx.author.id)

        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Config(bot))