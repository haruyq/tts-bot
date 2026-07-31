import discord
from discord.ext import commands
from discord import app_commands

import tts_client

from utils.db import set_connection
from utils.logger import Logger

Log = Logger(__name__)

class JoinCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="join", description="VCに接続し、読み上げを開始します。")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.guild.id)
    async def join(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        voice = interaction.user.voice
        
        if not voice:
            embed = discord.Embed(
                description="VCに接続してから実行してください。",
                color=discord.Colour.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        player = interaction.guild.voice_client
        if not player:
            player = await voice.channel.connect(cls=tts_client.Player, self_deaf=True)
            player.home = interaction.channel
            await set_connection(
                interaction.guild.id,
                voice.channel.id,
                interaction.channel.id,
            )
            
            embed = discord.Embed(
                description=f"{voice.channel.mention} に接続しました。",
                color=discord.Colour.green()
            )
            await interaction.followup.send(embed=embed)
            return
        
        embed = discord.Embed(
            description=f"既に {voice.channel.mention} に接続しています。",
            color=discord.Colour.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(JoinCommand(bot))
