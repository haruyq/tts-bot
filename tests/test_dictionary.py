from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

import discord
from discord import app_commands

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from commands.dictionary import DictionaryCommand, read_dictionary_file
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

class DictionaryImportTest(unittest.IsolatedAsyncioTestCase):
    async def test_import_replaces_only_target_dictionary(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
            db, "DB_PATH", Path(directory) / "main.db",
        ):
            await db.init_db()
            await db.set_dictionary(1, "既存", "きそん")
            await db.set_dictionary(1, "削除", "さくじょ")
            await db.set_dictionary(2, "別ユーザー", "べつゆーざー")
            await db.set_guild_dictionary(1, "既存", "きそん")
            await db.set_guild_dictionary(1, "削除", "さくじょ")
            await db.set_guild_dictionary(2, "別ギルド", "べつぎるど")

            data = '\ufeffword,reading\r\n既存,きぞん\r\n"単語,引用","読み""引用"\r\n'.encode("utf-8")
            file = SimpleNamespace(filename="dictionary.CSV", size=len(data), read=AsyncMock(return_value=data))
            interaction = SimpleNamespace(
                guild=SimpleNamespace(id=1),
                user=SimpleNamespace(id=1),
                response=SimpleNamespace(defer=AsyncMock()),
                followup=SimpleNamespace(send=AsyncMock()),
            )
            cog = DictionaryCommand(None)
            expected = [("既存", "きぞん"), ("単語,引用", '読み"引用')]

            await cog.dictionary_set.callback(cog, interaction, file=file)
            self.assertCountEqual(await db.get_dictionary(1), expected)
            self.assertCountEqual(await db.get_guild_dictionary(1), [("既存", "きそん"), ("削除", "さくじょ")])

            await cog.guild_dictionary_set.callback(cog, interaction, file=file)
            self.assertCountEqual(await db.get_guild_dictionary(1), expected)
            self.assertCountEqual(await db.get_dictionary(1), expected)
            self.assertEqual(await db.get_dictionary(2), [("別ユーザー", "べつゆーざー")])
            self.assertEqual(await db.get_guild_dictionary(2), [("別ギルド", "べつぎるど")])
            self.assertIn("2件", interaction.followup.send.call_args.args[0])

            await cog.dictionary_set.callback(cog, interaction, "追加", "ついか")
            self.assertCountEqual(await db.get_dictionary(1), expected + [("追加", "ついか")])

    async def test_invalid_csv_keeps_existing_dictionaries(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
            db, "DB_PATH", Path(directory) / "main.db",
        ):
            await db.init_db()
            await db.set_dictionary(1, "既存", "きそん")
            await db.set_guild_dictionary(1, "既存", "きそん")
            interaction = SimpleNamespace(
                guild=SimpleNamespace(id=1),
                user=SimpleNamespace(id=1),
                response=SimpleNamespace(defer=AsyncMock()),
                followup=SimpleNamespace(send=AsyncMock()),
            )
            cog = DictionaryCommand(None)
            cases = [
                (b"", "1行目"),
                (b"word,reading\n", "1件以上"),
                (b"reading,word\na,b\n", "1行目"),
                (b"word,reading\na,b\nc\n", "3行目"),
                (b"word,reading\na,b,c\n", "2行目"),
                (b"word,reading\n,b\n", "2行目"),
                (b"word,reading\na, \n", "2行目"),
                (b"word,reading\na,b\na,c\n", "重複"),
                (b'word,reading\na,b\nc,"unclosed', "3行目"),
                (b"word,reading\na,\x00\n", "使用できない文字"),
                ("word,reading\n単語,たんご\n".encode("cp932"), "UTF-8"),
                (b"x" * (1024 * 1024 + 1), "1MB"),
            ]

            for command in (cog.dictionary_set, cog.guild_dictionary_set):
                for data, error in cases:
                    with self.subTest(command=command.name, error=error, data=data[:30]):
                        file = SimpleNamespace(filename="dictionary.csv", size=0, read=AsyncMock(return_value=data))
                        await command.callback(cog, interaction, file=file)
                        self.assertIn(error, interaction.followup.send.call_args.args[0])
                        self.assertEqual(await db.get_dictionary(1), [("既存", "きそん")])
                        self.assertEqual(await db.get_guild_dictionary(1), [("既存", "きそん")])

                file = SimpleNamespace(filename="dictionary.csv", size=0, read=AsyncMock())
                for arguments in ({}, {"word": "単語"}, {"reading": "読み"}, {"word": "単語", "file": file}, {"reading": "読み", "file": file}):
                    await command.callback(cog, interaction, **arguments)
                    file.read.assert_not_awaited()
                    self.assertEqual(await db.get_dictionary(1), [("既存", "きそん")])
                    self.assertEqual(await db.get_guild_dictionary(1), [("既存", "きそん")])

    async def test_file_validation_and_download_failure(self):
        for filename, size in (("dictionary.txt", 1), ("dictionary.csv", 1024 * 1024 + 1)):
            file = SimpleNamespace(filename=filename, size=size, read=AsyncMock())
            with self.assertRaises(ValueError):
                await read_dictionary_file(file)
            file.read.assert_not_awaited()

        file = SimpleNamespace(
            filename="dictionary.csv",
            size=1,
            read=AsyncMock(side_effect=discord.HTTPException(SimpleNamespace(status=500, reason="Error"), "failed")),
        )
        with self.assertRaisesRegex(ValueError, "ファイルを取得できませんでした"):
            await read_dictionary_file(file)

    async def test_failed_replacement_keeps_existing_dictionary(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
            db, "DB_PATH", Path(directory) / "main.db",
        ):
            await db.init_db()
            for set_dictionary, replace_dictionary, get_dictionary in (
                (db.set_dictionary, db.replace_dictionary, db.get_dictionary),
                (db.set_guild_dictionary, db.replace_guild_dictionary, db.get_guild_dictionary),
            ):
                await set_dictionary(1, "既存", "きそん")
                with self.assertRaises(sqlite3.IntegrityError):
                    await replace_dictionary(1, [("追加", "ついか"), ("追加", "重複")])
                self.assertEqual(await get_dictionary(1), [("既存", "きそん")])

if __name__ == "__main__":
    unittest.main()
