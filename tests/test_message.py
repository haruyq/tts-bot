import asyncio
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

import tts_client

from events.message import MessageEvent, MessageSpeech
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
                guild=SimpleNamespace(id=index, voice_client=player),
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
        ), patch(
            "utils.filters.get_guild_dictionary",
            AsyncMock(side_effect=lambda guild_id: [("メッセージ", f"ギルド{guild_id}")]),
        ):
            event = MessageEvent(SimpleNamespace(process_commands=AsyncMock()))
            await asyncio.gather(*(
                event.on_message(message)
                for message in messages
            ))

        self.assertEqual(
            [player.queue.speeches[0].text for player in players],
            ["ギルド00", "ギルド11"],
        )

    async def test_replies_with_server_error_when_speech_fails(self):
        message = SimpleNamespace(
            channel=SimpleNamespace(send=AsyncMock()),
            to_reference=lambda **kwargs: "reference",
        )
        speech = MessageSpeech(text="こんにちは", plugin="p", speaker="s", message=message)
        event = MessageEvent(SimpleNamespace())

        await event.on_tts_speech_exception(SimpleNamespace(
            speech=speech,
            exception=tts_client.APIError(
                "speech_failed",
                "Connection timeout to host http://100.69.145.6:8765/v1/audio/speech, "
                "[Connect call failed ('100.69.145.6', 8765)]",
            ),
        ))
        await event.on_tts_speech_exception(SimpleNamespace(
            speech=speech,
            exception=tts_client.InvalidState("Player disconnected"),
        ))

        message.channel.send.assert_awaited_once_with(
            "Error: Connection timeout to host ***/v1/audio/speech, "
            "[Connect call failed ('***', 8765)]",
            reference="reference",
        )

if __name__ == "__main__":
    unittest.main()
