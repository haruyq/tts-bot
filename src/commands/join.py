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
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.guild.id)
    async def join(self, interaction: discord.Interaction):
        voice = interaction.user.voice
        
        if not voice:
            await interaction.response.send_message("VCに接続してから実行してください。", ephemeral=True)
            return
        
        player = interaction.guild.voice_client
        if not player:
            player = await voice.channel.connect(cls=tts_client.Player, self_deaf=True)
            player.home = interaction.channel 
            
            await interaction.response.send_message(f"{voice.channel.mention} に接続しました。({voice.channel.mention} <-> {interaction.channel.mention})")
            return
        
        await interaction.response.send_message(f"既に {voice.channel.mention} に接続しています。({voice.channel.mention} <-> {interaction.channel.mention})", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(JoinCommand(bot))
