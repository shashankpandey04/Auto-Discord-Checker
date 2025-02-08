import discord
from discord.abc import User
from discord.ext import commands, tasks

from pkgutil import iter_modules
import logging
import os
import time

from dotenv import load_dotenv
import motor.motor_asyncio

from Utils.prc import PRC_API_Client
from Utils.mongo import Document
from decouple import config

from Tasks.discord_check import discord_checks

load_dotenv()

intents = discord.Intents.default()
intents.presences = False
intents.message_content = True
intents.members = True
intents.messages = True
intents.moderation = True
intents.bans = True

discord.utils.setup_logging(level=logging.INFO)

class Bot(commands.AutoShardedBot):
    
    async def close(self):
        print('Closing...')
        await super().close()
        print('Closed!')
        
    def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.mongo = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGO_URI'))
            self.db = self.mongo["erlc_checker"]
            self.settings = self.db["settings"]

    async def setup_hook(self) -> None:
        self.prc_api = PRC_API_Client(self, base_url=config('PRC_API_URL'), api_key=config('PRC_API_KEY'))
        self.settings = Document(self.db, 'settings')
        
        Extensions = [m.name for m in iter_modules(['Cogs'],prefix='Cogs.')]

        for extension in Extensions:
            try:
                await self.load_extension(extension)
                logging.info(f'Loaded extension {extension}.')
            except Exception as e:
                logging.error(f'Failed to load extension {extension}.', exc_info=True)


        logging.info("Loaded all extensions.")

        logging.info("Connected to MongoDB")

        change_status.start()
        discord_checks.start(self)

        logging.info(f"Logged in as {bot.user}")

        await bot.tree.sync()


bot = Bot(
    command_prefix='d!',
    case_insensitive=True,
    intents=intents,
    help_command=None,
    allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True),
)


@tasks.loop(hours=1)
async def change_status():
    await bot.wait_until_ready()
    logging.info("Changing status")
    status = "ERLC Discord Checks"
    await bot.change_presence(
        activity=discord.CustomActivity(name=status)
    )

up_time = time.time()

def bot_ready():
    if bot.is_ready():
        return True
    return False

bot_token = os.getenv('BOT_TOKEN')

def run():
    try:
        bot.run(bot_token)
    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    run()