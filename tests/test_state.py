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
            guild=SimpleNamespace(name="Guild", voice_client=player),
        )
        before = SimpleNamespace(channel=player.channel)
        after = SimpleNamespace(channel=None)

        with patch("events.state.get_speaker", AsyncMock()) as get_speaker:
            await VoiceStateEvent(SimpleNamespace()).on_voice_state_update(member, before, after)

        player.disconnect.assert_awaited_once_with()
        player.play.assert_not_awaited()
        get_speaker.assert_not_awaited()

if __name__ == "__main__":
    unittest.main()
