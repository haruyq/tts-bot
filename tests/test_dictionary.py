from datetime import datetime, timezone
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

import discord
from discord import app_commands

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from commands.dictionary import DictionaryCommand
from utils import db
from utils.filters import apply_filters

class GuildDictionaryTest(unittest.IsolatedAsyncioTestCase):
    async def test_guild_dictionary_storage_and_user_priority(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
            db, "DB_PATH", Path(directory) / "main.db",
        ):
            await db.init_db()
            await db.set_dictionary(1, "共通", "ユーザー")
            await db.set_dictionary(1, "固定", "固定")
            await db.set_dictionary(1, "東京都", "とうきょうと")
            await db.set_guild_dictionary(1, "共通", "古い読み")
            await db.set_guild_dictionary(1, "共通", "ギルド")
            await db.set_guild_dictionary(1, "追加", "ついか")
            await db.set_guild_dictionary(1, "固定", "変更")
            await db.set_guild_dictionary(1, "東京", "とうきょう")
            await db.set_guild_dictionary(1, "ユーザー", "再置換")
            await db.set_guild_dictionary(1, "a.b", r"\1")
            await db.set_guild_dictionary(2, "共通", "別ギルド")
            await db.init_db()

            self.assertEqual(
                await apply_filters(1, "共通 追加 固定 東京都 a.b axb", 1),
                r"ユーザー ついか 固定 とうきょうと \1 axb",
            )
            self.assertEqual(await apply_filters(2, "共通 追加", 1), "ギルド ついか")
            self.assertEqual(await apply_filters(2, "共通 追加", 2), "別ギルド 追加")
            self.assertEqual(await apply_filters(1, "共通 追加"), "ユーザー 追加")
            self.assertEqual(await apply_filters(2, "共通", 3), "共通")

            interaction = SimpleNamespace(
                guild=SimpleNamespace(id=1),
                user=SimpleNamespace(id=2),
                response=SimpleNamespace(defer=AsyncMock()),
                followup=SimpleNamespace(send=AsyncMock()),
            )
            cog = DictionaryCommand(None)
            await cog.guild_dictionary_set.callback(cog, interaction, "登録", "とうろく")
            await cog.guild_dictionary_get.callback(cog, interaction)
            self.assertIn(
                "**登録** -> **とうろく**",
                interaction.followup.send.call_args.args[0],
            )
            await cog.guild_dictionary_remove.callback(cog, interaction, "登録")
            await cog.guild_dictionary_remove.callback(cog, interaction, "共通")

            self.assertNotIn(("登録", "とうろく"), await db.get_guild_dictionary(1))
            self.assertEqual(await apply_filters(2, "共通 追加", 1), "共通 ついか")
            self.assertEqual(await apply_filters(1, "共通", 1), "ユーザー")
            self.assertEqual(await db.get_guild_dictionary(2), [("共通", "別ギルド")])
            self.assertEqual(await db.get_dictionary(2), [])

    async def test_only_administrators_can_change_guild_dictionary(self):
        cog = DictionaryCommand(None)
        interaction = SimpleNamespace(
            guild=SimpleNamespace(id=1),
            permissions=discord.Permissions(manage_guild=True),
            created_at=datetime.now(timezone.utc),
            response=SimpleNamespace(send_message=AsyncMock()),
        )

        for command in (cog.guild_dictionary_set, cog.guild_dictionary_remove):
            self.assertTrue(command.guild_only)
            self.assertTrue(command.default_permissions.administrator)

            with self.assertRaises(app_commands.MissingPermissions) as error:
                await command._check_can_run(interaction)

            await cog.cog_app_command_error(interaction, error.exception)
            self.assertTrue(interaction.response.send_message.call_args.kwargs["ephemeral"])

            interaction.permissions.administrator = True
            self.assertTrue(await command._check_can_run(interaction))
            interaction.permissions.administrator = False

        self.assertTrue(cog.guild_dictionary_get.guild_only)
        self.assertTrue(await cog.guild_dictionary_get._check_can_run(interaction))

if __name__ == "__main__":
    unittest.main()
