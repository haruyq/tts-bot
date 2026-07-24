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
            class Queue:
                def __init__(self):
                    self.speeches = []

                async def put_wait(self, speech):
                    self.speeches.append(speech)

            def __init__(self, voice_channel, text_channel):
                self.channel = voice_channel
                self.home = text_channel
                self.queue = self.Queue()

        text_channels = [object(), object()]
        players = [
            Player(object(), text_channel)
            for text_channel in text_channels
        ]
        messages = [
            SimpleNamespace(
                author=SimpleNamespace(
                    bot=False,
                    id=index,
                ),
                guild=SimpleNamespace(voice_client=player),
                channel=text_channel,
                clean_content=f"メッセージ{index}",
                attachments=[],
                message_snapshots=[],
            )
            for index, (player, text_channel) in enumerate(zip(players, text_channels))
        ]

        with patch(
            "events.message.get_speaker",
            AsyncMock(return_value=("voicevox", "ずんだもん", "ノーマル")),
        ), patch(
            "utils.filters.get_dictionary",
            AsyncMock(return_value=[]),
        ):
            event = MessageEvent(SimpleNamespace(process_commands=AsyncMock()))
            await asyncio.gather(*(
                event.on_message(message)
                for message in messages
            ))

        self.assertEqual(
            [player.queue.speeches[0].text for player in players],
            ["メッセージ0", "メッセージ1"],
        )

if __name__ == "__main__":
    unittest.main()
