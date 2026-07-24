import discord
from discord.ext import commands
from discord import app_commands

import tts_client

from utils.filters import describe_attachments, apply_filters
from utils.db import get_speaker
from utils.logger import Logger

Log = Logger(__name__)

class ReadCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.context_menu(name="読み上げる")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.guild.id)
    async def read(self, interaction: discord.Interaction, message: discord.Message):
        player: tts_client.Player = interaction.guild.voice_client
        if not player:
            return
        
        if message.attachments:
            attachment_content = describe_attachments(message.attachments)
            content = f"{attachment_content}、{content}" if content else attachment_content

        speech_text = await apply_filters(message.author.id, content)
        plugin, speaker, style = await get_speaker(message.author.id)
        
        await player.play(tts_client.Speech(
            plugin=plugin,
            speaker=speaker,
            text=speech_text,
            style=style
        ))

async def setup(bot: commands.Bot):
    await bot.add_cog(ReadCommand(bot))
