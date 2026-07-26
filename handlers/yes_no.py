from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from config import settings
from handlers.common import play_shuffle, send_card_result
from handlers.nav import show_text
from keyboards.main import back_main, insufficient_funds_keyboard, yes_no_confirm
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


async def show_yes_no(
    target: Message | CallbackQuery,
    user_id: int,
    username: str | None = None,
    full_name: str | None = None,
) -> None:
    await db.ensure_user(user_id, username, full_name)
    user = await db.get_user(user_id)
    balance = user["balance"] if user else 0
    await show_text(
        target,
        f"{INTRO}\n\nТвой баланс: <b>{balance}</b> 💎",
        yes_no_confirm(),
    )


@router.callback_query(F.data == "goto:yesno")
async def yes_no_goto(callback: CallbackQuery) -> None:
    await show_yes_no(
        callback,
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.full_name,
    )


@router.callback_query(F.data == "yesno:draw")
async def yes_no_draw(callback: CallbackQuery) -> None:
    await callback.answer()
    user_id = callback.from_user.id
    await db.ensure_user(
        user_id, callback.from_user.username, callback.from_user.full_name
    )

    spent = await db.try_spend(user_id, settings.price_yes_no)
    if not spent:
        user = await db.get_user(user_id)
        balance = user["balance"] if user else 0
        await callback.message.answer(
            f"Не хватает баллов 💎\n"
            f"Нужно: <b>{settings.price_yes_no}</b>, у тебя: <b>{balance}</b>.",
            reply_markup=insufficient_funds_keyboard(),
            parse_mode="HTML",
        )
        return

    # Сразу убираем кнопку, чтобы не было повторных нажатий во время анимации
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await play_shuffle(callback.message)
    card = content.pick_yes_no_card()
    caption = content.format_yes_no_caption(card)
    number = int(card["number"])
    image = content.major_image_path(number)
    await send_card_result(
        callback.message,
        caption,
        image,
        upload_name=f"yesno_{number}.png",
    )
    answer = (card.get("answer") or "").strip()
    follow = f"🔮 Карта ответа: <b>{card['name']}</b>"
    if answer:
        follow += f"\n<b>{answer}</b>"
    await callback.message.answer(follow, reply_markup=back_main(), parse_mode="HTML")
