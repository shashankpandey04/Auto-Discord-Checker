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
        except KeyError:
            alert_channel = 0
            api_key = 0
            role_id = 0
            message = "You are not in the communication server. Please join it."

        self.alert_channel = discord.ui.ChannelSelect(
            placeholder="Select the alert channel",
            row=0,
            max_values=1,
            default_values=[discord.Object(id=alert_channel)],
            channel_types=[discord.ChannelType.text]
        )
        
        self.api_key_button = discord.ui.Button(
            label="API Key",
            style=discord.ButtonStyle.secondary,
            row=2
        )

        self.message_button = discord.ui.Button(
            label="Message",
            style=discord.ButtonStyle.secondary,
            row=2
        )

        self.alert_channel.callback = self.alert_channel_callback
        self.api_key_button.callback = self.api_key_button_callback
        self.message_button.callback = self.message_button_callback

        self.add_item(self.alert_channel)
        self.add_item(self.api_key_button)
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

    async def api_key_button_callback(self, interaction):
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
                title="API Key",
                description="Please send the API key in the chat.",
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

        self.sett["api_key"] = response.content
        await self.bot.settings.update_by_id(
            {
                "_id": self.sett["_id"],
                "api_key": response.content
            }
        )
        await response.delete()

        await interaction.followup.send(
            embed=discord.Embed(
                title="API Key Updated",
                description="The API key has been updated.",
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