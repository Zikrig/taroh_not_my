from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from config import settings
from handlers.common import play_shuffle, send_card_result
from keyboards.main import yes_no_confirm
from services import content
from services.db import db

router = Router()

INTRO = (
    "🪳 Я уже перемешал Старшие Арканы специально для тебя.\n\n"
    "Закрой глаза на мгновение, мысленно задай вопрос, на который можно ответить "
    "«Да» или «Нет», и нажми «Узнать ответ».\n"
    "🌿 Пусть сказочный лес откроет именно ту карту, которая нужна тебе сейчас. 🍃🔮\n\n"
    f"Стоимость: <b>{settings.price_yes_no}</b> баллов (1 балл = 1 ₽)."
)


async def show_yes_no(message: Message, user_id: int, username: str | None = None, full_name: str | None = None) -> None:
    await db.ensure_user(user_id, username, full_name)
    user = await db.get_user(user_id)
    balance = user["balance"] if user else 0
    await message.answer(
        f"{INTRO}\n\nТвой баланс: <b>{balance}</b> 💎",
        reply_markup=yes_no_confirm(),
        parse_mode="HTML",
    )


@router.message(F.text == "✅ Да / Нет")
async def yes_no_entry(message: Message) -> None:
    await show_yes_no(
        message,
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
    )


@router.callback_query(F.data == "goto:yesno")
async def yes_no_goto(callback: CallbackQuery) -> None:
    await callback.answer()
    await show_yes_no(
        callback.message,
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.full_name,
    )


@router.callback_query(F.data == "yesno:draw")
async def yes_no_draw(callback: CallbackQuery) -> None:
    await callback.answer()
    user_id = callback.from_user.id
    await db.ensure_user(user_id, callback.from_user.username, callback.from_user.full_name)

    spent = await db.try_spend(user_id, settings.price_yes_no)
    if not spent:
        user = await db.get_user(user_id)
        balance = user["balance"] if user else 0
        await callback.message.answer(
            f"Не хватает баллов 💎\n"
            f"Нужно: <b>{settings.price_yes_no}</b>, у тебя: <b>{balance}</b>.\n"
            "Пополни баланс через кнопку «💎 Баллы».",
            parse_mode="HTML",
        )
        return

    await play_shuffle(callback.message)
    card = content.pick_yes_no_card()
    caption = content.format_yes_no_caption(card)
    # yes/no uses major arcana numbers 0-21
    image = content.major_image_path(int(card["number"]))
    await send_card_result(callback.message, caption, image)
