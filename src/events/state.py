import discord
from discord.ext import commands

import tts_client

from utils.db import get_speaker, remove_connection
from utils.logger import Logger

Log = Logger(__name__)

class VoiceStateEvent(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot or (after.channel and before.channel == after.channel):
            return
        
        player: tts_client.Player = member.guild.voice_client
        if not player:
            return
        
        humans = [m for m in player.channel.members if not m.bot]
        if not humans:
            Log.debug(f"Auto disconnected from {player.channel.name} in {member.guild.name} due to no humans left.")
            await remove_connection(member.guild.id)
            await player.disconnect()
            return
        
        if (before.channel is None) == (after.channel is None):
            return
        
        action = "参加" if after.channel is not None else "退出"
        
        plugin, speaker, style = await get_speaker(member.id)
        
        await player.play(
            tts_client.Speech(
                f"{member.display_name}が{action}しました",
                plugin=plugin,
                speaker=speaker,
                options={"style": style} if style is not None else {},
            )
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceStateEvent(bot))
