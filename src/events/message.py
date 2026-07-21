import discord
from discord.ext import commands

import tts_client
import json
from pathlib import Path
import re

from utils.db import get_speaker
from utils.logger import Logger

Log = Logger(__name__)

with (Path(__file__).parents[1] / "emoji" / "emoji_ja.json").open(encoding="utf-8") as file:
    emoji_data = json.load(file)

EMOJI_READINGS = {
    emoji: data["short_name"]
    for emoji, data in emoji_data.items()
    if data["group"]
}
EMOJI_PATTERN = re.compile("|".join(map(re.escape, sorted(EMOJI_READINGS, key=len, reverse=True))))

def replace_emojis(text: str) -> str:
    return EMOJI_PATTERN.sub(lambda match: EMOJI_READINGS[match.group()], text.replace("\ufe0f", ""))

def describe_attachments(attachments: list[discord.Attachment]) -> str:
    counts = {
        "画像ファイル": 0,
        "動画ファイル": 0,
        "音声ファイル": 0,
        "文書ファイル": 0,
        "添付ファイル": 0,
    }

    for attachment in attachments:
        content_type = attachment.content_type or ""

        if content_type.startswith("image/"):
            counts["画像ファイル"] += 1
        elif content_type.startswith("video/"):
            counts["動画ファイル"] += 1
        elif content_type.startswith("audio/"):
            counts["音声ファイル"] += 1
        elif content_type.startswith("text/"):
            counts["文書ファイル"] += 1
        else:
            counts["添付ファイル"] += 1

    parts = [
        f"{file_type}{count}件"
        for file_type, count in counts.items()
        if count > 0
    ]

    return f"{'と'.join(parts)}が送信されました"

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
        
        if not message.channel == player.channel:
            return

        content = message.content.strip()
        
        if message.attachments:
            attachment_content = describe_attachments(message.attachments)
            content = f"{attachment_content}、{content}" if content else attachment_content
            
        if content == "s":
            await player.stop()
            return
        
        speech_text = replace_emojis(re.sub(r"https?://\S+", "リンク省略", content))
        plugin, speaker, style = await get_speaker(message.author.id)

        await player.play(tts_client.Speech(
            text=speech_text,
            plugin=plugin,
            speaker=speaker,
            options={"style": style} if style is not None else {},
        ))

async def setup(bot: commands.Bot):
    await bot.add_cog(MessageEvent(bot))
