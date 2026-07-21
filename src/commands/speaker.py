import asyncio

import discord
from discord import app_commands, ui
from discord.ext import commands

import tts_client

from utils.db import set_speaker, get_speaker
from utils.logger import Logger

Log = Logger(__name__)

class SpeakerCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _build_layout(self, speakers, styles, selection):
        plugin, speaker, style = selection
        if plugin not in speakers or not speakers[plugin]:
            plugin = next(
                (name for name, values in speakers.items() if values),
                "",
            )

        plugin_speakers = speakers.get(plugin, [])
        if speaker not in plugin_speakers:
            speaker = plugin_speakers[0] if plugin_speakers else ""

        page = plugin_speakers.index(speaker) // 25 if speaker else 0
        page_speakers = plugin_speakers[page * 25:(page + 1) * 25]
        available_styles = styles.get(plugin, {}).get(speaker, [])
        if style not in available_styles:
            style = available_styles[0] if available_styles else None

        container = ui.Container(accent_color=discord.Colour.blurple())

        container.add_item(ui.TextDisplay(
            f"**現在の話者: ** {speaker}"
            + (f" ({style})" if style is not None else "")
        ))

        plugin_pages = [
            (name, current_page, (len(values) + 24) // 25)
            for name, values in speakers.items()
            if values
            for current_page in range((len(values) + 24) // 25)
        ]
        plugin_select = ui.Select(
            placeholder="プラグインを選択してください",
            options=[
                discord.SelectOption(
                    label=(
                        name.upper()
                        if page_count == 1
                        else f"{name.upper()} ({current_page + 1}/{page_count})"
                    ),
                    value=str(index),
                    default=name == plugin and current_page == page,
                )
                for index, (name, current_page, page_count)
                in enumerate(plugin_pages)
            ] or [discord.SelectOption(label="利用可能なプラグインはありません")],
            disabled=not plugin_pages,
        )

        speaker_select = ui.Select(
            placeholder="話者を選択してください",
            options=[
                discord.SelectOption(
                    label=name,
                    default=name == speaker,
                )
                for name in page_speakers
            ] or [discord.SelectOption(label="利用可能な話者はありません")],
            disabled=not page_speakers,
        )

        style_select = ui.Select(
            placeholder="スタイルを選択してください",
            options=[
                discord.SelectOption(
                    label=name,
                    default=name == style,
                )
                for name in available_styles
            ] or [discord.SelectOption(label="利用可能なスタイルはありません")],
            disabled=not available_styles,
        )

        async def update(interaction, new_selection):
            await set_speaker(interaction.user.id, *new_selection)
            view = self._build_layout(speakers, styles, new_selection)
            await interaction.response.edit_message(view=view)

        async def select_plugin(interaction):
            selected_plugin, selected_page, _ = plugin_pages[
                int(plugin_select.values[0])
            ]
            selected_speakers = speakers[selected_plugin][
                selected_page * 25:(selected_page + 1) * 25
            ]
            selected_speaker = (
                speaker if speaker in selected_speakers else selected_speakers[0]
            )
            selected_styles = styles.get(selected_plugin, {}).get(
                selected_speaker,
                [],
            )
            selected_style = (
                style if style in selected_styles
                else selected_styles[0] if selected_styles else None
            )
            await update(
                interaction,
                (selected_plugin, selected_speaker, selected_style),
            )

        async def select_speaker(interaction):
            selected_speaker = speaker_select.values[0]
            selected_styles = styles.get(plugin, {}).get(selected_speaker, [])
            selected_style = (
                style if style in selected_styles
                else selected_styles[0] if selected_styles else None
            )
            await update(
                interaction,
                (plugin, selected_speaker, selected_style),
            )

        async def select_style(interaction):
            await update(
                interaction,
                (plugin, speaker, style_select.values[0]),
            )

        plugin_select.callback = select_plugin
        speaker_select.callback = select_speaker
        style_select.callback = select_style

        container.add_item(ui.ActionRow(plugin_select))
        container.add_item(ui.ActionRow(speaker_select))
        container.add_item(ui.ActionRow(style_select))

        view = ui.LayoutView()
        view.add_item(container)

        return view

    @app_commands.command(name="speaker", description="話者を変更します。")
    async def speaker(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        node = tts_client.Pool.get_node()
        speakers, styles, selection = await asyncio.gather(
            node.fetch_speakers(),
            node.fetch_styles(),
            get_speaker(interaction.user.id),
        )
        view = self._build_layout(speakers, styles, selection)
        await interaction.followup.send(view=view, ephemeral=True)
        
async def setup(bot: commands.Bot):
    await bot.add_cog(SpeakerCommand(bot))
