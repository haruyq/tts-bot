import discord
from discord.ext import commands

import tts_client
import re

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

        await player.play(tts_client.Speech(
            text=content,
            plugin="voicevox",
            speaker="東北きりたん",
            options={"style": "ノーマル"}
        ))

async def setup(bot: commands.Bot):
    await bot.add_cog(MessageEvent(bot))
