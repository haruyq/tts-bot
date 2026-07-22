import discord
from discord.ext import commands

import tts_client
import time

from utils.filters import apply_filters, describe_attachments
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
                
        player: tts_client.Player = message.guild.voice_client
        if not player:
            return
        
        if message.channel != player.channel:
            return

        content = message.clean_content
        attachments = message.attachments
        
        if content == "s":
            await player.stop()
            return
        
        if message.message_snapshots:
            for snapshot in message.message_snapshots:
                if snapshot.content:
                    content = "メッセージが転送されました。" + snapshot.content.strip()
                    attachments = snapshot.attachments
                    break
        
        if attachments:
            attachment_content = describe_attachments(attachments)
            content = f"{attachment_content}、{content}" if content else attachment_content
        
        speech_text = await apply_filters(message.author.id, content)
        plugin, speaker, style = await get_speaker(message.author.id)
        
        if not speech_text:
            return
        
        Log.debug(f"Speech queued: {speech_text} (plugin={plugin}, speaker={speaker}, style={style})")

        await player.queue.put_wait(tts_client.Speech(
            text=speech_text,
            plugin=plugin,
            speaker=speaker,
            options={"style": style} if style is not None else {},
        ))
        
        await self.bot.process_commands(message)

async def setup(bot: commands.Bot):
    await bot.add_cog(MessageEvent(bot))
