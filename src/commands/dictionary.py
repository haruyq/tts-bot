import discord
from discord.ext import commands
from discord import app_commands

import csv
import io

from utils.db import set_dictionary, remove_dictionary, get_dictionary
from utils.db import set_guild_dictionary, remove_guild_dictionary, get_guild_dictionary
from utils.db import replace_dictionary, replace_guild_dictionary
from utils.logger import Logger

Log = Logger(__name__)

async def read_dictionary_file(file: discord.Attachment) -> list[tuple[str, str]]:
    if not file.filename.lower().endswith(".csv"):
        raise ValueError("CSVファイルを指定してください。")

    if file.size > 1024 * 1024:
        raise ValueError("CSVファイルは1MB以下にしてください。")

    try:
        data = await file.read()
    except discord.HTTPException as e:
        raise ValueError("ファイルを取得できませんでした。もう一度添付してください。") from e

    if len(data) > 1024 * 1024:
        raise ValueError("CSVファイルは1MB以下にしてください。")

    try:
        reader = csv.reader(io.StringIO(data.decode("utf-8-sig"), newline=""), strict=True)
        if next(reader, None) != ["word", "reading"]:
            raise ValueError("CSVの1行目は「word,reading」にしてください。")

        dictionary = {}
        for row in reader:
            if not row:
                continue

            if len(row) != 2 or not all(value.strip() for value in row):
                raise ValueError(f"CSVの{reader.line_num}行目は、空でない単語と読みの2列にしてください。")

            if any("\x00" in value for value in row):
                raise ValueError(f"CSVの{reader.line_num}行目に使用できない文字が含まれています。")

            word, reading = row
            if word in dictionary:
                raise ValueError(f"CSVの{reader.line_num}行目の単語が重複しています。")

            dictionary[word] = reading
    except UnicodeDecodeError as e:
        raise ValueError("CSVファイルはUTF-8で保存してください。") from e
    except csv.Error as e:
        raise ValueError(f"CSVの{reader.line_num}行目を読み込めませんでした。CSVの形式を確認してください。") from e

    if not dictionary:
        raise ValueError("CSVに単語と読みを1件以上設定してください。")

    return list(dictionary.items())

class DictionaryCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="set-dictionary", description="辞書を設定します。")
    @app_commands.describe(file="UTF-8のCSV（1行目はword,reading）。あなたの辞書をすべて置き換えます。")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.guild.id)
    async def dictionary_set(self, interaction: discord.Interaction, word: str | None = None, reading: str | None = None, file: discord.Attachment | None = None):
        await interaction.response.defer(ephemeral=True)

        if file is not None:
            if word is not None or reading is not None:
                await interaction.followup.send("単語・読みとCSVファイルは同時に指定できません。", ephemeral=True)
                return

            try:
                dictionary = await read_dictionary_file(file)
            except ValueError as e:
                await interaction.followup.send(str(e), ephemeral=True)
                return

            await replace_dictionary(interaction.user.id, dictionary)
            await interaction.followup.send(f"CSVから辞書を{len(dictionary)}件に置き換えました。", ephemeral=True)
            return

        if word is None or reading is None:
            await interaction.followup.send("単語と読み、またはCSVファイルを指定してください。", ephemeral=True)
            return
        
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

    @app_commands.command(name="set-guild-dictionary", description="ギルド辞書を設定します。")
    @app_commands.describe(file="UTF-8のCSV（1行目はword,reading）。このギルドの辞書をすべて置き換えます。")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.guild.id)
    @app_commands.checks.has_permissions(administrator=True)
    async def guild_dictionary_set(self, interaction: discord.Interaction, word: str | None = None, reading: str | None = None, file: discord.Attachment | None = None):
        await interaction.response.defer(ephemeral=True)

        if file is not None:
            if word is not None or reading is not None:
                await interaction.followup.send("単語・読みとCSVファイルは同時に指定できません。", ephemeral=True)
                return

            try:
                dictionary = await read_dictionary_file(file)
            except ValueError as e:
                await interaction.followup.send(str(e), ephemeral=True)
                return

            await replace_guild_dictionary(interaction.guild.id, dictionary)
            await interaction.followup.send(f"CSVからギルド辞書を{len(dictionary)}件に置き換えました。", ephemeral=True)
            return

        if word is None or reading is None:
            await interaction.followup.send("単語と読み、またはCSVファイルを指定してください。", ephemeral=True)
            return

        await set_guild_dictionary(interaction.guild.id, word, reading)

        await interaction.followup.send(f"ギルド辞書を設定しました。 **{word}** -> **{reading}**", ephemeral=True)

    @app_commands.command(name="remove-guild-dictionary", description="ギルド辞書を削除します。")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.guild.id)
    @app_commands.checks.has_permissions(administrator=True)
    async def guild_dictionary_remove(self, interaction: discord.Interaction, word: str):
        await interaction.response.defer(ephemeral=True)

        await remove_guild_dictionary(interaction.guild.id, word)

        await interaction.followup.send(f"ギルド辞書を削除しました。 **{word}** -> **変更なし**", ephemeral=True)

    @app_commands.command(name="get-guild-dictionary", description="ギルド辞書を取得します。")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.guild.id)
    async def guild_dictionary_get(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        dictionary = await get_guild_dictionary(interaction.guild.id)

        if not dictionary:
            await interaction.followup.send("ギルド辞書は設定されていません。", ephemeral=True)
            return

        dictionary_str = "\n".join([f"**{word}** -> **{reading}**" for word, reading in dictionary])
        await interaction.followup.send(dictionary_str, ephemeral=True)

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("ギルド辞書の変更には管理者権限が必要です。", ephemeral=True)
            return

        raise error

async def setup(bot: commands.Bot):
    await bot.add_cog(DictionaryCommand(bot))
