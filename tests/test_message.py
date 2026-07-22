import asyncio
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from events.message import MessageEvent
from utils.filters import replace_emojis

class EmojiReplacementTest(unittest.TestCase):
    def test_replaces_emoji_with_japanese_reading(self):
        self.assertEqual(
            replace_emojis("こんにちは😀❤️👨‍⚕️"),
            "こんにちはにっこり笑う赤いハート男性の医者",
        )

class MessageEventTest(unittest.IsolatedAsyncioTestCase):
    async def test_routes_messages_to_each_guild_player(self):
        class Player:
            def __init__(self, channel):
                self.channel = channel
                self.speeches = []

            async def play(self, speech):
                self.speeches.append(speech)

        players = [Player(object()), Player(object())]
        messages = [
            SimpleNamespace(
                author=SimpleNamespace(
                    bot=False,
                    id=index,
                ),
                guild=SimpleNamespace(voice_client=player),
                channel=player.channel,
                clean_content=f"メッセージ{index}",
                attachments=[],
                message_snapshots=[],
            )
            for index, player in enumerate(players)
        ]

        with patch(
            "events.message.get_speaker",
            AsyncMock(return_value=("voicevox", "ずんだもん", "ノーマル")),
        ), patch(
            "utils.filters.get_dictionary",
            AsyncMock(return_value=[]),
        ):
            await asyncio.gather(*(
                MessageEvent(None).on_message(message)
                for message in messages
            ))

        self.assertEqual(
            [player.speeches[0].text for player in players],
            ["メッセージ0", "メッセージ1"],
        )

if __name__ == "__main__":
    unittest.main()
