import discord
import asyncio

BLANK_COLOR = 0x2b2d31
blank_color = BLANK_COLOR

class ConfigurationMenu(discord.ui.View):
    def __init__(self, bot, sett, user_id):
        super().__init__()
        self.bot = bot
        self.sett = sett
        self.user_id = user_id

        try:
            alert_channel = self.sett.get("alert_channel", 0)
            api_key = self.sett.get("api_key", 0)
            role_id = self.sett.get("role_id", 0)
            message = self.sett.get("message", "You are not in the communication server. Please join it.")
            minimum_players = self.sett.get("minimum_players", 0)
        except KeyError:
            alert_channel = 0
            api_key = 0
            role_id = 0
            message = "You are not in the communication server. Please join it."
            minimum_players = 0

        self.alert_channel = discord.ui.ChannelSelect(
            placeholder="Select the alert channel",
            row=0,
            max_values=1,
            default_values=[discord.Object(id=alert_channel)],
            channel_types=[discord.ChannelType.text]
        )
        
        self.minimum_player_button = discord.ui.Button(
            label="Minimum Players",
            style=discord.ButtonStyle.secondary,
            row=2
        )

        self.message_button = discord.ui.Button(
            label="Message",
            style=discord.ButtonStyle.secondary,
            row=2
        )

        self.alert_channel.callback = self.alert_channel_callback
        self.minimum_player_button.callback = self.minimum_players_callback
        self.message_button.callback = self.message_button_callback

        self.add_item(self.alert_channel)
        self.add_item(self.minimum_player_button)
        self.add_item(self.message_button)

    async def alert_channel_callback(self, interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You cannot configure this setting.",
                    color=BLANK_COLOR
                ),
                ephemeral=True
            )
        
        self.sett["alert_channel"] = interaction.data["values"][0]
        await self.bot.settings.update_by_id(
            {
                "_id": self.sett["_id"],
                "alert_channel": interaction.data["values"][0]
            }
        )

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Alert Channel Updated",
                description="The alert channel has been updated.",
                color=BLANK_COLOR
            ),
            ephemeral=True
        )

    async def minimum_players_callback(self, interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You cannot configure this setting.",
                    color=BLANK_COLOR
                ),
                ephemeral=True
            )

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Minimum Players",
                description="Please provide the minimum number of players required to start the alert.",
                color=BLANK_COLOR
            ),
            ephemeral=True
        )

        try:
            response = await self.bot.wait_for(
                "message",
                check=lambda m: m.author.id == self.user_id,
                timeout=60
            )
        except asyncio.TimeoutError:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Timeout",
                    description="You took too long to provide the API key.",
                    color=BLANK_COLOR
                )
            )

        self.sett["minimum_players"] = int(response.content)
        await self.bot.settings.update_by_id(
            {
                "_id": self.sett["_id"],
                "minimum_players": int(response.content)
            }
        )
        await response.delete()

        await interaction.followup.send(
            embed=discord.Embed(
                title="Minimum Players Updated",
                description="The minimum players required has been updated.",
                color=BLANK_COLOR
            ),
            ephemeral=True
        )

    async def message_button_callback(self, interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You cannot configure this setting.",
                    color=BLANK_COLOR
                ),
                ephemeral=True
            )

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Message",
                description="Please provide the message that will be sent to the user.",
                color=BLANK_COLOR
            ),
            ephemeral=True
        )

        try:
            response = await self.bot.wait_for(
                "message",
                check=lambda m: m.author.id == self.user_id,
                timeout=60
            )
        except asyncio.TimeoutError:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Timeout",
                    description="You took too long to provide the message.",
                    color=BLANK_COLOR
                )
            )

        self.sett["message"] = response.content
        await self.bot.settings.update_by_id(
            {
                "_id": self.sett["_id"],
                "message": response.content
            }
        )
        await response.delete()

        await interaction.followup.send(
            embed=discord.Embed(
                title="Message Updated",
                description="The message has been updated.",
                color=BLANK_COLOR
            ),
            ephemeral=True
        )

    
async def setup(bot):
    await bot.add_cog(ConfigurationMenu(bot))