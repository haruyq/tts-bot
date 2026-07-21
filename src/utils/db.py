import aiosqlite
from pathlib import Path

from utils.config import get_config

config = get_config()

DB_PATH = Path("data/main.db")

async def init_db() -> None:
    DB_PATH.parent.mkdir(exist_ok=True)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_speakers (
                user_id INTEGER PRIMARY KEY,
                plugin TEXT NOT NULL,
                speaker TEXT NOT NULL,
                style TEXT
            )
        """)
        cursor = await db.execute("PRAGMA table_info(user_speakers)")
        columns = {row[1] for row in await cursor.fetchall()}

        if "plugin" not in columns:
            await db.execute(
                "ALTER TABLE user_speakers "
                "ADD COLUMN plugin TEXT NOT NULL DEFAULT 'voicevox'"
            )

        if "style" not in columns:
            await db.execute(
                "ALTER TABLE user_speakers "
                "ADD COLUMN style TEXT DEFAULT 'ノーマル'"
            )

        await db.commit()

async def set_speaker(
    user_id: int,
    plugin: str,
    speaker: str,
    style: str | None,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO user_speakers (user_id, plugin, speaker, style)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                plugin = excluded.plugin,
                speaker = excluded.speaker,
                style = excluded.style
            """,
            (user_id, plugin, speaker, style),
        )
        await db.commit()

async def get_speaker(
    user_id: int,
) -> tuple[str, str, str | None]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT plugin, speaker, style
            FROM user_speakers
            WHERE user_id = ?
            """,
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()

    if row is not None:
        return row[0], row[1], row[2]

    return (
        config.default_plugin,
        config.default_speaker,
        config.default_style,
    )
