import discord
from discord.ext import commands

import tts_client
import os

from utils.db import init_db
from utils.config import get_config
from utils.logger import ColorFormatter, Logger

config = get_config()
Log = Logger(__name__)

BASE_DIR = os.path.dirname(__file__)

class TTSBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=">>>>", intents=intents, help_command=None)

    async def load_cogs(self):
        for f in os.listdir(os.path.join(BASE_DIR, 'commands')):
            if f.endswith('.py'):
                ext = f"commands.{f[:-3]}"
                try:
                    await self.load_extension(ext)
                    Log.info(f"[{ext}] Loaded")
                except Exception as e:
                    Log.error(f"[{ext}] Failed to Load: {e}")

        for f in os.listdir(os.path.join(BASE_DIR, 'events')):
            if f.endswith('.py'):
                ext = f"events.{f[:-3]}"
                try:
                    await self.load_extension(ext)
                    Log.info(f"[{ext}] Loaded")
                except Exception as e:
                    Log.error(f"[{ext}] Failed to Load: {e}")

    async def setup_hook(self):
        await init_db()

        await self.load_cogs()
        await tts_client.Pool.connect(
            nodes=[
                tts_client.Node(
                    config.tts_base_url,
                    password=config.tts_password,
                    identifier="main",
                ),
            ],
            client=self,
        )
    
    async def close(self):
        await tts_client.Pool.close()
        await super().close()
        
if __name__ == "__main__":
    TTSBot().run(config.token, log_formatter=ColorFormatter())
