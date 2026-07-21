import discord
from discord.ext import commands

import tts_client
import re

from utils.db import get_speaker
from utils.logger import Logger

Log = Logger(__name__)

class MessageEvent(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        
        if not message.guild:
            return

        if not message.content:
            return
        
        player: tts_client.Player = message.guild.voice_client
        if not player:
            return
        
        content = re.sub(r"https?://\S+", "リンク省略", message.content)
        plugin, speaker, style = await get_speaker(message.author.id)

        if content == "s":
            await player.stop()
            return

        await player.play(tts_client.Speech(
            text=content,
            plugin=plugin,
            speaker=speaker,
            options={"style": style} if style is not None else {},
        ))

async def setup(bot: commands.Bot):
    await bot.add_cog(MessageEvent(bot))
