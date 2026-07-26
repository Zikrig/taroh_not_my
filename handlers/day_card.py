from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from handlers.common import card_by_id, play_shuffle, send_card_result, today_key
from services import content
from services.db import db

router = Router()


async def deliver_day_card(message: Message) -> None:
    user_id = message.from_user.id
    day = today_key()
    picked = content.pick_day_card(user_id, day)
    card_id, is_new = await db.get_or_create_day_card(user_id, day, picked["id"])
    card = card_by_id(card_id) or picked

    if is_new:
        await play_shuffle(message)

    caption = content.format_day_card_caption(card)
    await send_card_result(message, caption, content.card_image_path(card["id"]))


@router.message(Command("card"))
@router.message(F.text == "🃏 Карта дня")
async def day_card_button(message: Message) -> None:
    await db.ensure_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
    )
    await deliver_day_card(message)
