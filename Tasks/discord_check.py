import datetime
import re
import time
import discord
import pytz
from discord.ext import tasks
import logging
import asyncio

from Utils.constants import BLANK_COLOR
from Utils.prc import ServerPlayers
from Utils import prc

@tasks.loop(minutes=2, reconnect=True)
async def discord_checks(bot):
    start_time = time.time()
    logging.warning("[ITERATE] Starting Discord Check Iteration")
    total_guilds = 0
    
    async for guild_data in bot.settings.db.find():
        try:
            guild_id = guild_data["guild_id"] or guild_data["_id"]
            
            # Fetch guild info
            try:
                guild = await bot.fetch_guild(guild_id)
            except discord.errors.NotFound:
                logging.warning(f"[ITERATE] Guild with ID {guild_id} not found")
                continue

            # Fetch players
            try:
                players: list[ServerPlayers] = await bot.prc_api._fetch_server_players(guild_id)
            except prc.ResponseFailed:
                logging.error(f"[ITERATE] PRC ResponseFailure for guild {guild_id}")
                continue
                
            logging.info(f"[ITERATE] Checking {len(players)} players in guild {guild_id}")

            # Check minimum players requirement
            total_players = len(players)
            minimum_players = guild_data.get("minimum_players", 0)
            if total_players < minimum_players:
                logging.warning(f"[ITERATE] Not enough players in guild {guild_id} ({total_players}/{minimum_players})")
                continue

            # Get alert channel
            alert_channel = None
            if "alert_channel" in guild_data:
                try:
                    alert_channel = guild.get_channel(guild_data["alert_channel"])
                except discord.errors.NotFound:
                    logging.warning(f"[ITERATE] Alert channel not found in guild {guild_id}")

            # Create Discord embed
            embed = discord.Embed(
                title="Players Not in Discord",
                color=BLANK_COLOR,
                timestamp=datetime.datetime.now(pytz.utc),
            )
            
            # Pre-compile member name patterns for more efficient matching
            member_patterns = {
                member: [
                    re.compile(re.escape(name), re.IGNORECASE)
                    for name in [member.name, member.display_name, getattr(member, 'global_name', '') or '']
                    if name
                ]
                for member in guild.members
            }

            # Process players and track those not in Discord
            not_in_discord = []
            embed_description = []

            for player in players:
                player_name, player_id = player.Player.split(":")
                
                # Check if player matches any member's names
                member_found = any(
                    any(pattern.search(player_name) for pattern in patterns)
                    for patterns in member_patterns.values()
                )

                if not member_found:
                    not_in_discord.append(player_name)
                    embed_description.append(f"> [{player_name}](https://roblox.com/users/{player_id}/profile)")

            # Update embed description
            embed.description = "\n".join(embed_description) if embed_description else "> All players are in the Discord server."
            
            # Set embed author
            embed.set_author(
                name=guild.name,
                icon_url=guild.icon
            )

            # Only send PM command if there are players not in Discord
            if not_in_discord:
                message = f":pm {','.join(not_in_discord)} {guild_data['message']}"
                await bot.prc_api._send_command(guild_id, message)

            # Send embed to alert channel if it exists
            if alert_channel:
                try:
                    await alert_channel.send(embed=embed)
                except (discord.errors.Forbidden, discord.errors.NotFound, discord.errors.HTTPException) as e:
                    logging.warning(f"[ITERATE] Failed to send message in guild {guild_id}: {str(e)}")

        except Exception as e:
            logging.error(f"[ITERATE] Error in guild {guild_id}: {e}")
            continue

        total_guilds += 1
        await asyncio.sleep(2)  # Using asyncio.sleep instead of time.sleep

    end_time = time.time()
    logging.warning(f"[ITERATE] Discord Check Iteration finished in {end_time - start_time} seconds")
    logging.warning(f"[ITERATE] Next Discord Check Iteration in 2 minutes")
    logging.warning(f"[ITERATE] Checked {total_guilds} guilds")