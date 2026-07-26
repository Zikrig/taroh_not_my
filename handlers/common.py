from __future__ import annotations

import asyncio
import random
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram.types import FSInputFile, Message

from config import settings
from services import content


async def play_shuffle(message: Message) -> None:
    """Как в ТЗ: сообщения по очереди появляются и исчезают, потом карта."""
    steps = [
        "🪲 Жучки перемешивают колоду..",
        "✨ Светлячки освещают путь к ответу..",
        "🔮 Последний штрих волшебства..",
    ]
    for step in steps:
        msg = await message.answer(step)
        # Чуть дольше и с лёгким разбросом, чтобы не было «метронома»
        await asyncio.sleep(random.uniform(1.0, 2.5))
        try:
            await msg.delete()
        except Exception:
            pass
    await asyncio.sleep(random.uniform(0.3, 0.7))


def today_key() -> str:
    return datetime.now(ZoneInfo(settings.tz)).date().isoformat()


def current_year() -> int:
    return datetime.now(ZoneInfo(settings.tz)).year


async def send_card_result(
    message: Message,
    caption: str,
    image_path=None,
    *,
    upload_name: str | None = None,
) -> None:
    # Telegram: caption у фото ≤ 1024, обычное сообщение ≤ 4096
    if image_path is not None and image_path.exists():
        # ASCII-имя при загрузке — надёжнее в Docker/Linux с кириллическими путями
        name = upload_name or image_path.name
        try:
            photo = FSInputFile(image_path, filename=name)
            if len(caption) <= 1024:
                await message.answer_photo(photo, caption=caption, parse_mode="HTML")
            else:
                await message.answer_photo(photo)
                await message.answer(caption, parse_mode="HTML")
            return
        except Exception:
            pass
    await message.answer(caption, parse_mode="HTML")


def card_by_id(card_id: str) -> dict | None:
    for card in content.day_cards():
        if card["id"] == card_id:
            return card
    return None
