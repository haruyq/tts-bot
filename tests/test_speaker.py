from contextlib import closing
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from commands.speaker import SpeakerCommand
from utils import db

class SpeakerLayoutTest(unittest.TestCase):
    def test_selects_saved_speaker_page(self):
        speakers = {"voicevox": [f"話者{i}" for i in range(26)]}
        styles = {"voicevox": {"話者25": ["ノーマル"]}}
        view = SpeakerCommand(None)._build_layout(
            speakers,
            styles,
            ("voicevox", "話者25", "ノーマル"),
        )
        components = view.to_components()

        self.assertEqual(
            components[0]["components"][1]["components"][0]["options"][1]["label"],
            "VOICEVOX (2/2)",
        )

class DatabaseTest(unittest.IsolatedAsyncioTestCase):
    async def test_dictionary_keeps_multiple_words(self):
        original_path = db.DB_PATH

        with tempfile.TemporaryDirectory() as directory:
            db.DB_PATH = Path(directory) / "main.db"

            try:
                with closing(sqlite3.connect(db.DB_PATH)) as connection:
                    connection.execute("""
                        CREATE TABLE dictionary (
                            user_id INTEGER PRIMARY KEY,
                            word TEXT NOT NULL,
                            reading TEXT NOT NULL
                        )
                    """)
                    connection.execute(
                        "INSERT INTO dictionary VALUES (?, ?, ?)",
                        (1, "既存", "きそん"),
                    )
                    connection.commit()

                await db.init_db()
                await db.set_dictionary(1, "追加", "ついか")

                self.assertCountEqual(
                    await db.get_dictionary(1),
                    [("既存", "きそん"), ("追加", "ついか")],
                )
            finally:
                db.DB_PATH = original_path

    async def test_migrates_existing_speaker(self):
        original_path = db.DB_PATH

        with tempfile.TemporaryDirectory() as directory:
            db.DB_PATH = Path(directory) / "main.db"

            try:
                with closing(sqlite3.connect(db.DB_PATH)) as connection:
                    connection.execute("""
                        CREATE TABLE user_speakers (
                            user_id INTEGER PRIMARY KEY,
                            speaker TEXT NOT NULL
                        )
                    """)
                    connection.execute(
                        "INSERT INTO user_speakers VALUES (?, ?)",
                        (1, "ずんだもん"),
                    )
                    connection.commit()

                await db.init_db()

                self.assertEqual(
                    await db.get_speaker(1),
                    ("voicevox", "ずんだもん", "ノーマル"),
                )
            finally:
                db.DB_PATH = original_path

if __name__ == "__main__":
    unittest.main()
