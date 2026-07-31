import discord
from discord.ext import commands
from discord import app_commands

from utils.db import set_dictionary, remove_dictionary, get_dictionary
from utils.logger import Logger

Log = Logger(__name__)

class DictionaryCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="set-dictionary", description="辞書を設定します。")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.guild.id)
    async def dictionary_set(self, interaction: discord.Interaction, word: str, reading: str):
        await interaction.response.defer(ephemeral=True)
        
        await set_dictionary(interaction.user.id, word, reading)
        
        await interaction.followup.send(f"辞書を設定しました。 **{word}** -> **{reading}**", ephemeral=True)
    
    @app_commands.command(name="remove-dictionary", description="辞書を削除します。")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.guild.id)
    async def dictionary_remove(self, interaction: discord.Interaction, word: str):
        await interaction.response.defer(ephemeral=True)
        
        await remove_dictionary(interaction.user.id, word)
        
        await interaction.followup.send(f"辞書を削除しました。 **{word}** -> **変更なし**", ephemeral=True)
    
    @app_commands.command(name="get-dictionary", description="辞書を取得します。")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.guild.id)
    async def dictionary_get(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        dictionary = await get_dictionary(interaction.user.id)
        
        if not dictionary:
            await interaction.followup.send("辞書は設定されていません。", ephemeral=True)
            return
        
        dictionary_str = "\n".join([f"**{word}** -> **{reading}**" for word, reading in dictionary])
        await interaction.followup.send(dictionary_str, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(DictionaryCommand(bot))
