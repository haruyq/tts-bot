import discord
from discord.ext import commands

import tts_client
import re
import time

from utils.filters import replace_emojis, describe_attachments, replace_dict_words
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
        
        start = time.perf_counter()
        
        player: tts_client.Player = message.guild.voice_client
        if not player:
            return
        
        voice = message.author.voice
        if not voice or voice.channel != player.channel:
            return

        content = message.content.strip()
        
        if content == "s":
            await player.stop()
            return
        
        if message.attachments:
            attachment_content = describe_attachments(message.attachments)
            content = f"{attachment_content}、{content}" if content else attachment_content
        
        speech_text = replace_emojis(re.sub(r"https?://\S+", "リンク省略", content))
        plugin, speaker, style = await get_speaker(message.author.id)
        
        if not speech_text:
            return

        speech_text = await replace_dict_words(message.author.id, speech_text)

        await player.play(tts_client.Speech(
            text=speech_text,
            plugin=plugin,
            speaker=speaker,
            options={"style": style} if style is not None else {},
        ))
        
        end = time.perf_counter()

        result = (end - start) * 1000
        Log.debug(f"Speech request took: {result:.2f} ms")

async def setup(bot: commands.Bot):
    await bot.add_cog(MessageEvent(bot))
