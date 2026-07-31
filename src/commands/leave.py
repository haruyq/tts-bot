import discord
from discord.ext import commands
from discord import app_commands

import tts_client

from utils.db import remove_connection
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
            embed = discord.Embed(
                description="VCに接続してから実行してください。",
                color=discord.Colour.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        player = interaction.guild.voice_client
        await remove_connection(interaction.guild.id)

        if not player:
            embed = discord.Embed(
                description="BotはVCに接続していません。",
                color=discord.Colour.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        await player.disconnect()
        embed = discord.Embed(
            description="切断しました。",
            color=discord.Colour.green()
        )
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(LeaveCommand(bot))
