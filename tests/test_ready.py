from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

import tts_client

from events.ready import ReadyEvent
from utils import db

class ReadyEventTest(unittest.IsolatedAsyncioTestCase):
    async def test_restores_saved_connection_once(self):
        original_path = db.DB_PATH

        with tempfile.TemporaryDirectory() as directory:
            db.DB_PATH = Path(directory) / "main.db"

            try:
                await db.init_db()
                await db.set_connection(1, 2, 3)

                player = SimpleNamespace()
                voice_channel = SimpleNamespace(
                    name="Voice",
                    connect=AsyncMock(return_value=player),
                )
                text_channel = object()
                guild = SimpleNamespace(name="Guild", voice_client=None)
                channels = {
                    2: voice_channel,
                    3: text_channel,
                }
                bot = SimpleNamespace(
                    tree=SimpleNamespace(sync=AsyncMock()),
                    user=SimpleNamespace(name="Bot", id=4),
                    get_guild=Mock(return_value=guild),
                    get_channel=Mock(side_effect=channels.get),
                )
                event = ReadyEvent(bot)

                await event.on_ready()
                await event.on_ready()

                voice_channel.connect.assert_awaited_once_with(
                    cls=tts_client.Player,
                    self_deaf=True,
                )
                self.assertIs(player.home, text_channel)

                await db.remove_connection(1)
                self.assertEqual(await db.get_connections(), [])
            finally:
                db.DB_PATH = original_path

if __name__ == "__main__":
    unittest.main()
