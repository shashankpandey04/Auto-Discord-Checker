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
    await asyncio.sleep(5)
    async for guild_data in bot.settings.db.find():
        try:
            guild_id = guild_data["guild_id"] or guild_data["_id"]
            
            try:
                guild = await bot.fetch_guild(guild_id)
            except discord.errors.NotFound:
                logging.warning(f"[ITERATE] Guild with ID {guild_id} not found")
                continue

            try:
                players: list[ServerPlayers] = await bot.prc_api._fetch_server_players(guild_id)
            except prc.ResponseFailed:
                logging.error(f"[ITERATE] PRC ResponseFailure for guild {guild_id}")
                continue
                
            logging.info(f"[ITERATE] Checking {len(players)} players in guild {guild_id}")

            total_players = len(players)
            minimum_players = guild_data.get("minimum_players", 0)
            if total_players < minimum_players:
                logging.warning(f"[ITERATE] Not enough players in guild {guild_id} ({total_players}/{minimum_players})")
                continue

            try:
                alert_channel = guild.get_channel(guild_data["alert_channel"])
            except discord.errors.NotFound:
                logging.warning(f"[ITERATE] Alert channel not found in guild {guild_id}")

            embed = discord.Embed(
                title="Players Not in Discord",
                color=BLANK_COLOR,
                timestamp=datetime.datetime.now(pytz.utc),
            )
            embed.description = ""

            not_in_discord = []

            def normalize_name(name):
                """Removes special characters and converts to lowercase for better matching."""
                return re.sub(r'[^a-zA-Z0-9]', '', name).lower()

            for player in players:
                player_name = normalize_name(player.Player.split(":")[0])  # Extract and normalize
                player_id = player.Player.split(":")[1]

                member_found = False

                for member in guild.members:
                    discord_names = [
                        normalize_name(member.name).lower(),
                        normalize_name(member.display_name).lower(),
                        normalize_name(getattr(member, 'global_name', '')).lower()
                    ]

                    # Check if the player_name is contained within any of the Discord names
                    for name in discord_names:
                        if player_name in name:
                            member_found = True
                            break

                if not member_found:
                    #logging.info(f"[ITERATE] Player {player_name} not found in guild {guild_id}")
                    embed.description += f"> [{player_name}](https://roblox.com/users/{player_id}/profile)\n"
                    not_in_discord.append(player_name)


            if embed.description == "":
                embed.description = "> All players are in the Discord server."

            embed.set_author(
                name=guild.name,
                icon_url=guild.icon
            )

            if not_in_discord:
                message = f":pm {','.join(not_in_discord)} {guild_data['message']}"
                #await bot.prc_api._send_command(guild_id, message)
            logging.info(f"[ITERATE] Sent command to {len(not_in_discord)} players in guild {guild_id}")

            try:
                if alert_channel:
                    #await alert_channel.send(embed=embed)
                    pass
            except discord.errors.Forbidden:
                logging.warning(f"[ITERATE] Missing permissions to send messages in guild {guild_id}")
            except discord.errors.NotFound:
                logging.warning(f"[ITERATE] Alert channel not found in guild {guild_id}")
            except discord.errors.HTTPException:
                logging.warning(f"[ITERATE] Failed to send message in guild {guild_id}")

        except Exception as e:
            logging.error(f"[ITERATE] Error in guild {guild_id}: {e}")
            continue

        total_guilds += 1
        await asyncio.sleep(2)  # Using asyncio.sleep instead of time.sleep

    end_time = time.time()
    logging.warning(f"[ITERATE] Discord Check Iteration finished in {end_time - start_time} seconds")
    logging.warning(f"[ITERATE] Next Discord Check Iteration in 2 minutes")
    logging.warning(f"[ITERATE] Checked {total_guilds} guilds")