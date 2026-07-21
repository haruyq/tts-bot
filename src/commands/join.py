import discord
from discord.ext import commands
from discord import app_commands

import tts_client

from utils.logger import Logger

Log = Logger(__name__)

class JoinCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="join", description="VCに接続し、読み上げを開始します。")
    async def join(self, interaction: discord.Interaction):
        voice = interaction.user.voice
        
        if not voice:
            await interaction.response.send_message("VCに接続してから実行してください。", ephemeral=True)
            return
        
        if not interaction.guild.voice_client:
            await voice.channel.connect(cls=tts_client.Player)
            await interaction.response.send_message("VCに接続しました。")

async def setup(bot: commands.Bot):
    await bot.add_cog(JoinCommand(bot))
