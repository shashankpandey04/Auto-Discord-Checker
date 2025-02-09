import datetime
import re
import time
import discord
import pytz
from discord.ext import tasks
import logging
import asyncio
import random

from Utils.constants import BLANK_COLOR
from Utils.prc import ServerPlayers
from Utils import prc

def extract_username_from_pattern(name: str) -> list[str]:
    """
    Extract possible usernames from different Discord name patterns.
    Examples:
    - "OnDuty | Username" -> ["onduty", "username"]
    - "[PD] Username" -> ["pd", "username"]
    - "Username | Patrol" -> ["username", "patrol"]
    """
    # Convert to lowercase for case-insensitive matching
    name = name.lower()
    
    # Split by common separators
    parts = re.split(r'[\s|\-_\[\]{}()]+', name)
    
    # Remove empty strings and common prefixes/words
    return [part for part in parts if part and len(part) > 1]

@tasks.loop(minutes=2, reconnect=True)
async def discord_checks(bot):
    start_time = time.time()
    logging.warning("[ITERATE] Starting Discord Check Iteration")
    total_guilds = 0
    
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
            total_checked = 0

            # Pre-process member names
            member_usernames = {}
            for member in guild.members:
                # Get all possible names for the member
                names = [
                    member.name,
                    member.display_name,
                    getattr(member, 'global_name', '') or ''
                ]
                
                # Extract possible usernames from each name
                for name in names:
                    if name:
                        extracted_names = extract_username_from_pattern(name)
                        member_usernames.update({name.lower(): extracted_names for name in extracted_names})

            for player in players:
                if not player.get('Player'):
                    continue
                    
                total_checked += 1
                player_name = player['Player'].split(":")[0]
                player_id = player['Player'].split(":")[1]
                
                # Convert player name to lowercase and extract possible usernames
                player_parts = extract_username_from_pattern(player_name)
                
                # Check if any part of the player's name matches any part of any member's name
                member_found = False
                for player_part in player_parts:
                    if player_part in member_usernames or any(
                        player_part in username_parts 
                        for username_parts in member_usernames.values()
                    ):
                        member_found = True
                        break

                if not member_found:
                    embed.description += f"> [{player_name}](https://roblox.com/users/{player_id}/profile)\n"
                    not_in_discord.append(player_name)
                    logging.debug(f"[ITERATE] Player {player_name} not found in Discord for guild {guild_id}")

            logging.info(f"[ITERATE] Checked {total_checked} players, found {len(not_in_discord)} not in Discord for guild {guild_id}")

            if not not_in_discord:
                embed.description = "> All players are in the Discord server."
                logging.info(f"[ITERATE] All players are in Discord for guild {guild_id}")
            else:
                # Only send PM command if there are players not in Discord
                message = f":pm {','.join(not_in_discord)} {guild_data['message']}"
                logging.info(f"[ITERATE] Sending PM command for {len(not_in_discord)} players in guild {guild_id}")
                await bot.prc_api._send_command(guild_id, message)

            embed.set_author(
                name=guild.name,
                icon_url=guild.icon
            )

            try:
                if alert_channel:
                    await alert_channel.send(embed=embed)
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
        # Random sleep between 5-10 seconds between guild checks
        sleep_time = random.uniform(5, 10)
        logging.info(f"[ITERATE] Sleeping for {sleep_time:.2f} seconds before next guild check")
        await asyncio.sleep(sleep_time)

    end_time = time.time()
    logging.warning(f"[ITERATE] Discord Check Iteration finished in {end_time - start_time} seconds")
    logging.warning(f"[ITERATE] Next Discord Check Iteration in 2 minutes")
    logging.warning(f"[ITERATE] Checked {total_guilds} guilds")