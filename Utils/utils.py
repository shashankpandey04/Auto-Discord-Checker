from discord.ext import commands
from datetime import  timedelta
import re
import requests

async def get_prefix(bot, message):
    """
    Get the prefix for the bot.
    :param bot (Bot): The bot.
    :param message (discord.Message): The message.
    :return (str): The prefix.
    """
    settings = await bot.settings.get(message.guild.id)
    
    if settings is None:
        return commands.when_mentioned_or("?")(bot,message)
    try:
        customization = settings.get("customization")
        if customization is None:
            return commands.when_mentioned_or("?")(bot,message)
        prefix = customization.get("prefix")
        if prefix is None:
            return commands.when_mentioned_or("?")(bot,message)
        return prefix
    except KeyError:
        return commands.when_mentioned_or("?")(bot,message)


def discord_time(dt):
    """
    Convert a datetime object to a Discord timestamp.
    :param dt (datetime): The datetime object.
    :return (str): The Discord timestamp.
    """
    # Convert datetime to a Unix timestamp
    unix_timestamp = int(dt.timestamp())
    # Return the Discord formatted timestamp
    return f"<t:{unix_timestamp}:R>"

        
def parse_duration(duration):
    """
    Parse a duration string and return the total duration in seconds.
    Supports days (d), weeks (w), hours (h), minutes (m), and seconds (s).
    """
    regex = r"(?:(\d+)\s*d(?:ays?)?)?\s*(?:(\d+)\s*w(?:eeks?)?)?\s*(?:(\d+)\s*h(?:ours?)?)?\s*(?:(\d+)\s*m(?:inutes?)?)?\s*(?:(\d+)\s*s(?:econds?)?)?"
    matches = re.match(regex, duration)
    if not matches:
        return None

    days = int(matches.group(1)) if matches.group(1) else 0
    weeks = int(matches.group(2)) if matches.group(2) else 0
    hours = int(matches.group(3)) if matches.group(3) else 0
    minutes = int(matches.group(4)) if matches.group(4) else 0
    seconds = int(matches.group(5)) if matches.group(5) else 0

    total_seconds = timedelta(days=days, weeks=weeks, hours=hours, minutes=minutes, seconds=seconds).total_seconds()
    return int(total_seconds)
