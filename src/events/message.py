import discord
from discord.ext import commands

import tts_client
import re
import time
from dataclasses import dataclass, field

from utils.filters import apply_filters, describe_attachments
from utils.db import get_speaker
from utils.logger import Logger

Log = Logger(__name__)

# バックエンドのアドレスをDiscordに出さない (URLはパスを残し、スキームからポートまでを隠す)
_ADDRESS = re.compile(r"https?://[^/\s]+|\b\d{1,3}(?:\.\d{1,3}){3}(?::\d+)?\b")

@dataclass(frozen=True)
class MessageSpeech(tts_client.Speech):
    """読み上げ元のメッセージを持たせ、合成失敗時に返信できるようにする"""
    message: discord.Message | None = field(default=None, compare=False)

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
        
        if message.channel != getattr(player, "home", None):
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
        
        try:
            speech_text = await apply_filters(message.author.id, content, message.guild.id)
            plugin, speaker, style = await get_speaker(message.author.id)
            
            if not speech_text:
                return
            
            Log.debug(f"Speech queued: {speech_text} (plugin={plugin}, speaker={speaker}, style={style})")

            await player.queue.put_wait(MessageSpeech(
                text=speech_text,
                plugin=plugin,
                speaker=speaker,
                options={"style": style} if style is not None else {},
                message=message,
            ))
            
        except Exception as e:
            Log.error(f"Error processing message: {e}")
            await message.reply(f"Error: {e}")
        
        await self.bot.process_commands(message)

    @commands.Cog.listener()
    async def on_tts_speech_exception(self, payload: tts_client.SpeechExceptionEventPayload):
        message = getattr(payload.speech, "message", None)

        if message is None or not isinstance(payload.exception, tts_client.APIError):
            return

        Log.error(f"Speech failed: {payload.exception}")
        await message.channel.send(
            f"Error: {_ADDRESS.sub('***', payload.exception.message)}",
            reference=message.to_reference(fail_if_not_exists=False),
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(MessageEvent(bot))
