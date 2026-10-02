from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from events.state import VoiceStateEvent

class VoiceStateEventTest(unittest.IsolatedAsyncioTestCase):
    async def test_does_not_play_after_auto_disconnect(self):
        player = SimpleNamespace(
            channel=SimpleNamespace(name="Voice", members=[]),
            disconnect=AsyncMock(),
            play=AsyncMock(),
        )
        member = SimpleNamespace(
            bot=False,
            guild=SimpleNamespace(id=1, name="Guild", voice_client=player),
        )
        before = SimpleNamespace(channel=player.channel)
        after = SimpleNamespace(channel=None)

        with patch(
            "events.state.remove_connection",
            AsyncMock(),
        ) as remove_connection, patch(
            "events.state.get_speaker",
            AsyncMock(),
        ) as get_speaker:
            await VoiceStateEvent(SimpleNamespace()).on_voice_state_update(member, before, after)

        remove_connection.assert_awaited_once_with(member.guild.id)
        player.disconnect.assert_awaited_once_with()
        player.play.assert_not_awaited()
        get_speaker.assert_not_awaited()

    async def test_queues_join_announcement_instead_of_playing(self):
        player = SimpleNamespace(
            channel=SimpleNamespace(name="Voice", members=[SimpleNamespace(bot=False)]),
            queue=SimpleNamespace(put_wait=AsyncMock()),
            play=AsyncMock(),
        )
        member = SimpleNamespace(
            bot=False,
            display_name="Alice",
            id=2,
            guild=SimpleNamespace(id=1, name="Guild", voice_client=player),
        )
        before = SimpleNamespace(channel=None)
        after = SimpleNamespace(channel=player.channel)

        with patch(
            "events.state.get_speaker",
            AsyncMock(return_value=("plugin", "speaker", None)),
        ):
            await VoiceStateEvent(SimpleNamespace()).on_voice_state_update(member, before, after)

        player.play.assert_not_awaited()
        speech = player.queue.put_wait.await_args.args[0]
        self.assertEqual(speech.text, "Aliceが参加しました")

if __name__ == "__main__":
    unittest.main()
