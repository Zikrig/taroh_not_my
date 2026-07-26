from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import settings
from handlers.common import current_year, play_shuffle, send_card_result
from handlers.nav import show_text
from handlers.states import MoneyStates
from keyboards.main import (
    back_main,
    cancel_input_keyboard,
    insufficient_funds_keyboard,
    money_actions,
    year_picker,
)
from services import content
from services.db import db
from services.numerology import calc_energy_number

router = Router()

INTRO = (
    "💰 Хочешь финансового изобилия? Прогноз покажет возможности на год. "
    "Ты поймёшь, куда направить внимание и как эффективнее управлять ресурсами.\n\n"
    "Дата рождения сохраняется в разделе «Другое» — бот сам рассчитает цифру "
    "(можно выбрать другой год).\n\n"
    f"Стоимость: <b>{settings.price_money}</b> баллов."
)


async def show_money(
    target: Message | CallbackQuery,
    user_id: int,
    username: str | None = None,
    full_name: str | None = None,
) -> None:
    await db.ensure_user(user_id, username, full_name)
    birth = await db.get_birth_date(user_id)
    user = await db.get_user(user_id)
    balance = user["balance"] if user else 0
    birth_line = (
        f"📅 Дата рождения: <b>{birth.strftime('%d.%m.%Y')}</b>\n"
        if birth
        else "📅 Дата рождения ещё не указана — нажми кнопку ниже.\n"
    )
    await show_text(
        target,
        f"{INTRO}\n\n{birth_line}Баланс: <b>{balance}</b> 💎",
        money_actions(bool(birth)),
    )


@router.callback_query(F.data == "goto:money")
async def money_goto(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await show_money(
        callback,
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.full_name,
    )


@router.callback_query(F.data == "money:pick_year")
async def money_pick_year(callback: CallbackQuery) -> None:
    await show_text(
        callback,
        "Выбери год для прогноза:",
        year_picker("money", current_year()),
    )


@router.callback_query(F.data == "money:year_input")
async def money_year_input(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(MoneyStates.waiting_year)
    await callback.message.answer(
        "Напиши год числом, например: <code>2027</code>",
        reply_markup=cancel_input_keyboard("goto:money"),
        parse_mode="HTML",
    )


@router.message(MoneyStates.waiting_year)
async def money_year_typed(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not (text.isdigit() and 1900 <= int(text) <= 2100):
        await message.answer(
            "Нужен год от 1900 до 2100.",
            reply_markup=cancel_input_keyboard("goto:money"),
        )
        return
    await state.clear()
    await _calc_and_send(message, message.from_user.id, int(text))


@router.callback_query(F.data.startswith("money:calc:"))
async def money_calc(callback: CallbackQuery) -> None:
    await callback.answer()
    raw = callback.data.split(":")[-1]
    year = current_year() if raw == "current" else int(raw)
    await _calc_and_send(callback.message, callback.from_user.id, year)


async def _calc_and_send(message: Message, user_id: int, year: int) -> None:
    birth = await db.get_birth_date(user_id)
    if not birth:
        await message.answer(
            "Сначала укажи дату рождения — это можно сделать в «Другое».",
            reply_markup=money_actions(False),
        )
        return

    spent = await db.try_spend(user_id, settings.price_money)
    if not spent:
        user = await db.get_user(user_id)
        balance = user["balance"] if user else 0
        await message.answer(
            f"Не хватает баллов 💎\n"
            f"Нужно: <b>{settings.price_money}</b>, у тебя: <b>{balance}</b>.",
            reply_markup=insufficient_funds_keyboard(),
            parse_mode="HTML",
        )
        return

    number = calc_energy_number(birth, year)
    item = content.money_forecast().get(number)
    if not item:
        await message.answer(
            "Не удалось найти описание прогноза.",
            reply_markup=back_main(),
        )
        return

    await play_shuffle(message)
    caption = content.format_money_caption(item, year, number)
    await send_card_result(message, caption, content.major_image_path(number))
    await message.answer("Выбери действие 🍃", reply_markup=back_main())
