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
from Utils.utils import get_discord_by_roblox
from Utils import prc


@tasks.loop(minutes=5, reconnect=True)
async def discord_checks(bot):
    start_time = time.time()
    logging.warning("[ITERATE] Starting Discord Check Iteration")

    async for guild_data in bot.settings.db.find(
        {
            "api_key": {"$exists": True, "$ne": None},
        }
    ):
        guild_id = guild_data["_id"]
        try:
            guild = bot.get_guild(guild_id)
        except discord.errors.NotFound:
            logging.warning(f"[ITERATE] Guild with ID {guild_id} not found")
            continue
        try:
            players: list[ServerPlayers] = await bot.prc_api._fetch_server_players(guild_id)
        except prc.ResponseFailed:
            logging.error(f"PRC ResponseFailure for guild {guild_id}")
            continue
        logging.info(f"[ITERATE] Checking {len(players)} players in guild {guild_id}")

        total_players = len(players)
        minimum_players = guild_data["minimum_players"] if "minimum_players" in guild_data else 0
        if total_players < minimum_players:
            logging.warning(f"[ITERATE] Not enough players in guild {guild_id} ({total_players}/{minimum_players})")
            continue
        
        alert_channel_id = guild_data["alert_channel"]
        try:
            alert_channel = guild.get_channel(alert_channel_id)
        except discord.errors.NotFound:
            logging.warning(f"[ITERATE] Alert channel with ID {alert_channel_id} not found in guild {guild_id}")
            continue

        embed = discord.Embed(
            title="Players Not in Discord",
            color=BLANK_COLOR,
            timestamp=datetime.datetime.now(pytz.utc),
        )

        not_in_discord = []

        for player in players:
            pattern = re.compile(re.escape(player.username), re.IGNORECASE)
            member_found = False

            for member in guild.members:
                if pattern.search(member.name) or pattern.search(member.display_name) or (hasattr(member, 'global_name') and member.global_name and pattern.search(member.global_name)):
                    member_found = True
                    break

            if not member_found:
                try:
                    discord_id = await get_discord_by_roblox(bot, player.username)
                    if discord_id:
                        member = guild.get_member(discord_id)
                        if member:
                            member_found = True
                except discord.HTTPException:
                    pass

            if not member_found:
                embed.description += f"> [{player.username}](https://roblox.com/users/{player.id}/profile)\n"
                not_in_discord.append(player.username)

        if embed.description == "":
            embed.description = "> All players are in the Discord server."

        embed.set_author(
            name=guild.name,
            icon_url=guild.icon
        )

        message = f":pm {','.join(not_in_discord)} {guild_data['message']}"
        response = await bot.prc_api._send_command(guild_id, message)
        if response.status == 200:
            logging.info(f"[ITERATE] Sent message to {guild_id} with response {response}")
        else:
            logging.error(f"[ITERATE] Failed to send message to {guild_id} with response {response}")
        
        try:
        
            await alert_channel.send(embed=embed)
        except discord.errors.Forbidden:
            logging.warning(f"[ITERATE] Missing permissions to send messages in alert channel {alert_channel_id} in guild {guild_id}")
        except discord.errors.NotFound:
            logging.warning(f"[ITERATE] Alert channel with ID {alert_channel_id} not found in guild {guild_id}")
        except discord.errors.HTTPException:
            logging.warning(f"[ITERATE] Failed to send message in alert channel {alert_channel_id} in guild {guild_id}")

        time.sleep(1)

    end_time = time.time()
    logging.warning(f"[ITERATE] Discord Check Iteration finished in {end_time - start_time} seconds")
    logging.warning(f"[ITERATE] Next Discord Check Iteration in 2 minutes")
                        
