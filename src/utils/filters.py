import discord
import json
import re
from pathlib import Path
from utils.db import get_dictionary

with (Path(__file__).parents[1] / "emoji" / "emoji_ja.json").open(encoding="utf-8") as file:
    emoji_data = json.load(file)

EMOJI_READINGS = {
    emoji: data["short_name"]
    for emoji, data in emoji_data.items()
    if data["group"]
}
EMOJI_PATTERN = re.compile("|".join(map(re.escape, sorted(EMOJI_READINGS, key=len, reverse=True))))

def replace_emojis(text: str) -> str:
    return EMOJI_PATTERN.sub(lambda match: EMOJI_READINGS[match.group()], text.replace("\ufe0f", ""))

def describe_attachments(attachments: list[discord.Attachment]) -> str:
    counts = {
        "画像ファイル": 0,
        "動画ファイル": 0,
        "音声ファイル": 0,
        "文書ファイル": 0,
        "添付ファイル": 0,
    }

    for attachment in attachments:
        content_type = attachment.content_type or ""

        if content_type.startswith("image/"):
            counts["画像ファイル"] += 1
        elif content_type.startswith("video/"):
            counts["動画ファイル"] += 1
        elif content_type.startswith("audio/"):
            counts["音声ファイル"] += 1
        elif content_type.startswith("text/"):
            counts["文書ファイル"] += 1
        else:
            counts["添付ファイル"] += 1

    parts = [
        f"{file_type}{count}件"
        for file_type, count in counts.items()
        if count > 0
    ]

    return f"{'と'.join(parts)}が送信されました"

async def replace_dict_words(user_id: int, text: str) -> str:
    user_dictionary = dict(await get_dictionary(user_id))

    for word, reading in user_dictionary.items():
        text = text.replace(word, reading)

    return text

async def default_replace_dict_words(text: str) -> str:
    default_dictionary = {
        "@": "あて、",
    }

    for word, reading in default_dictionary.items():
        text = text.replace(word, reading)

    return text