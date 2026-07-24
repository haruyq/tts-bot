from discord.ext import commands

import tts_client

from utils.db import get_connections
from utils.logger import Logger

Log = Logger(__name__)

class ReadyEvent(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.restored = False

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.restored:
            self.restored = True

            for guild_id, voice_channel_id, text_channel_id in await get_connections():
                guild = self.bot.get_guild(guild_id)

                if not guild:
                    Log.error(f"Failed to reconnect in guild {guild_id}: guild not found.")
                    continue

                if guild.voice_client:
                    continue

                voice_channel = self.bot.get_channel(voice_channel_id)
                text_channel = self.bot.get_channel(text_channel_id)

                if not voice_channel or not text_channel:
                    Log.error(f"Failed to reconnect in {guild.name}: channel not found.")
                    continue

                try:
                    player = await voice_channel.connect(cls=tts_client.Player, self_deaf=True)
                    player.home = text_channel
                    Log.info(f"Reconnected to {voice_channel.name} in {guild.name}.")
                except Exception as e:
                    Log.error(f"Failed to reconnect in {guild.name}: {e}")

        await self.bot.tree.sync()
        Log.info(f"Logged in as {self.bot.user.name} ({self.bot.user.id})")

async def setup(bot: commands.Bot):
    await bot.add_cog(ReadyEvent(bot))
