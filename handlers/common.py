from __future__ import annotations

import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram.types import FSInputFile, Message

from config import settings
from services import content


async def play_shuffle(message: Message) -> None:
    steps = [
        "🪲 Жучки перемешивают колоду..",
        "✨ Светлячки освещают путь к ответу..",
        "🔮 Последний штрих волшебства..",
    ]
    msg = await message.answer(steps[0])
    for step in steps[1:]:
        await asyncio.sleep(0.9)
        try:
            await msg.edit_text(step)
        except Exception:
            await message.answer(step)
    await asyncio.sleep(0.7)
    try:
        await msg.delete()
    except Exception:
        pass


def today_key() -> str:
    return datetime.now(ZoneInfo(settings.tz)).date().isoformat()


def current_year() -> int:
    return datetime.now(ZoneInfo(settings.tz)).year


async def send_card_result(
    message: Message,
    caption: str,
    image_path=None,
) -> None:
    # Telegram: caption у фото ≤ 1024, обычное сообщение ≤ 4096
    if image_path is not None and image_path.exists():
        photo = FSInputFile(image_path)
        if len(caption) <= 1024:
            await message.answer_photo(photo, caption=caption, parse_mode="HTML")
        else:
            await message.answer_photo(photo)
            await message.answer(caption, parse_mode="HTML")
    else:
        await message.answer(caption, parse_mode="HTML")


def card_by_id(card_id: str) -> dict | None:
    for card in content.day_cards():
        if card["id"] == card_id:
            return card
    return None
