from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from handlers.common import card_by_id, play_shuffle, send_card_result, today_key
from keyboards.main import main_menu
from services import content
from services.db import db

router = Router()


async def deliver_day_card(message: Message, user_id: int) -> None:
    day = today_key()
    picked = content.pick_day_card(user_id, day)
    card_id, is_new = await db.get_or_create_day_card(user_id, day, picked["id"])
    card = card_by_id(card_id) or picked

    await play_shuffle(message)

    caption = content.format_day_card_caption(card)
    await send_card_result(message, caption, content.card_image_path(card["id"]))

    if is_new:
        followup = (
            f"✨ <b>Твоя карта дня — {card['name']}</b>\n"
            "Колода обновится завтра в 00:00. До встречи в сказочном лесу! 🍃🔮"
        )
    else:
        followup = (
            f"🃏 <b>Твоя карта дня на сегодня — {card['name']}</b>\n"
            "Она уже с тобой до полуночи. Загляни снова завтра за новой 🌿"
        )
    await message.answer(followup, reply_markup=main_menu(), parse_mode="HTML")


@router.message(Command("card"))
async def day_card_command(message: Message) -> None:
    await db.ensure_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
    )
    await deliver_day_card(message, message.from_user.id)


@router.callback_query(F.data == "menu:daycard")
async def day_card_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    await db.ensure_user(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.full_name,
    )
    await deliver_day_card(callback.message, callback.from_user.id)
