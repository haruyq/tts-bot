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
        await db.execute("""
            CREATE TABLE IF NOT EXISTS dictionary (
                user_id INTEGER NOT NULL,
                word TEXT NOT NULL,
                reading TEXT NOT NULL,
                PRIMARY KEY (user_id, word)
            )
        """)

        async with db.execute("PRAGMA table_info(dictionary)") as cursor:
            dictionary_columns = await cursor.fetchall()

        if [column[1] for column in dictionary_columns if column[5]] == ["user_id"]:
            await db.execute("ALTER TABLE dictionary RENAME TO old_dictionary")
            await db.execute("""
                CREATE TABLE dictionary (
                    user_id INTEGER NOT NULL,
                    word TEXT NOT NULL,
                    reading TEXT NOT NULL,
                    PRIMARY KEY (user_id, word)
                )
            """)
            await db.execute("""
                INSERT INTO dictionary (user_id, word, reading)
                SELECT user_id, word, reading FROM old_dictionary
            """)
            await db.execute("DROP TABLE old_dictionary")

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

async def set_dictionary(
    user_id: int,
    word: str,
    reading: str,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO dictionary (user_id, word, reading)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, word) DO UPDATE SET
                reading = excluded.reading
            """,
            (user_id, word, reading),
        )
        await db.commit()

async def remove_dictionary(
    user_id: int,
    word: str,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            DELETE FROM dictionary
            WHERE user_id = ? AND word = ?
            """,
            (user_id, word),
        )
        await db.commit()

async def get_dictionary(
    user_id: int,
) -> list[tuple[str, str]]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT word, reading
            FROM dictionary
            WHERE user_id = ?
            """,
            (user_id,),
        ) as cursor:
            rows = await cursor.fetchall()

    return rows
