import discord
from discord.ext import commands
from discord import app_commands

import aiohttp

from utils.filters import describe_attachments, apply_filters
from utils.config import get_config
from utils.db import get_speaker
from utils.logger import Logger

config = get_config()

Log = Logger(__name__)

class SynthesizeCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.context_menu(name="TTSを作成")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.guild.id)
    async def synthesize(self, interaction: discord.Interaction, message: discord.Message):
        await interaction.response.defer()

        if message.attachments:
            attachment_content = describe_attachments(message.attachments)
            content = f"{attachment_content}、{content}" if content else attachment_content

        speech_text = await apply_filters(message.author.id, content)
        plugin, speaker, style = await get_speaker(message.author.id)
        
        data = {
            "plugin": plugin,
            "speaker": speaker,
            "text": speech_text,
            "style": style
        }
        
        headers = {
            "Authorization": f"Bearer {config.tts_password}"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{config.tts_base_url}/api/synthesize", json=data, headers=headers) as resp:
                if resp.status == 200:
                    audio_data = await resp.read()
                    await interaction.followup.send(file=discord.File(fp=audio_data, filename="tts.wav"))
                else:
                    Log.error(f"Failed to synthesize TTS: {resp.status} - {await resp.text()}")
                    await interaction.followup.send(f"生成に失敗しました。\nHTTP: {resp.status}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(SynthesizeCommand(bot))
