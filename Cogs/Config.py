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
        ).add_field(
            name="Minimum Players",
            value=f"{"No Minimum Players" if not sett.get("minimum_players") else sett['minimum_players']}"
        )

        view = ConfigurationMenu(self.bot, sett, ctx.author.id)

        await ctx.send(embed=embed, view=view)

    @commands.guild_only()
    @commands.hybrid_command()
    async def link(self, ctx, key:str):
        """
        Link the bot to the PRC API.
        """
        
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You need to have the administrator permission to run this command.",
                    color=0x2F3136
                )
            )
        
        check = await self.bot.prc_api._send_test_request(ctx.guild.id, key)
        if not check:
            return await ctx.send(
                embed=discord.Embed(
                    title="Invalid API Key",
                    description="The API key provided is invalid.",
                    color=0x2F3136
                )
            )

        doc = {
            "_id": ctx.guild.id,
            "api_key": key
        }

        await self.bot.settings.update_by_id(doc)

        message = await ctx.send(
            embed=discord.Embed(
                title="API Key Added",
                description="The API key has been added.",
                color=0x2F3136
            )
        )
        await message.delete()
        await ctx.channel.send(
            embed=discord.Embed(
                title="API Key Added",
                description="The API key has been added.",
                color=0x2F3136
            )
        )
        


async def setup(bot):
    await bot.add_cog(Config(bot))