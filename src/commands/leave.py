import discord
from discord.ext import commands
from discord import app_commands

import tts_client

from utils.logger import Logger

Log = Logger(__name__)

class LeaveCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="leave", description="VCから切断します。")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.guild.id)
    async def leave(self, interaction: discord.Interaction):
        voice = interaction.user.voice
        
        if not voice:
            await interaction.response.send_message("VCに接続してから実行してください。", ephemeral=True)
            return
        
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("VCから切断しました。")

async def setup(bot: commands.Bot):
    await bot.add_cog(LeaveCommand(bot))
