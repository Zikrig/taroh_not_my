from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import settings
from handlers.common import current_year, play_shuffle, send_card_result
from handlers.nav import show_text
from handlers.states import EnergyStates
from keyboards.main import (
    back_main,
    cancel_input_keyboard,
    energy_actions,
    insufficient_funds_keyboard,
    year_picker,
)
from services import content
from services.db import db
from services.numerology import calc_energy_number

router = Router()

INTRO = (
    "🪳 Хочешь узнать, какая энергия будет сопровождать тебя в этом году? 🌿✨\n\n"
    "Каждый год проходит под влиянием своей энергии. Понимая её, легче принимать решения, "
    "обходить трудности и замечать возможности. 🍀\n\n"
    "Дата рождения сохраняется в разделе «Другое» — бот сам рассчитает цифру "
    "(можно выбрать другой год).\n\n"
    f"Стоимость расчёта: <b>{settings.price_energy}</b> баллов."
)


async def show_energy(
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
        energy_actions(bool(birth)),
    )


@router.callback_query(F.data == "goto:energy")
async def energy_goto(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await show_energy(
        callback,
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.full_name,
    )


@router.callback_query(F.data == "energy:pick_year")
async def energy_pick_year(callback: CallbackQuery) -> None:
    await show_text(
        callback,
        "Выбери год для расчёта:",
        year_picker("energy", current_year()),
    )


@router.callback_query(F.data == "energy:year_input")
async def energy_year_input(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(EnergyStates.waiting_year)
    await callback.message.answer(
        "Напиши год числом, например: <code>2027</code>",
        reply_markup=cancel_input_keyboard("goto:energy"),
        parse_mode="HTML",
    )


@router.message(EnergyStates.waiting_year)
async def energy_year_typed(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not (text.isdigit() and 1900 <= int(text) <= 2100):
        await message.answer(
            "Нужен год от 1900 до 2100.",
            reply_markup=cancel_input_keyboard("goto:energy"),
        )
        return
    await state.clear()
    await _calc_and_send(message, message.from_user.id, int(text))


@router.callback_query(F.data.startswith("energy:calc:"))
async def energy_calc(callback: CallbackQuery) -> None:
    await callback.answer()
    raw = callback.data.split(":")[-1]
    year = current_year() if raw == "current" else int(raw)
    await _calc_and_send(callback.message, callback.from_user.id, year)


async def _calc_and_send(message: Message, user_id: int, year: int) -> None:
    birth = await db.get_birth_date(user_id)
    if not birth:
        await message.answer(
            "Сначала укажи дату рождения — это можно сделать в «Другое».",
            reply_markup=energy_actions(False),
        )
        return

    spent = await db.try_spend(user_id, settings.price_energy)
    if not spent:
        user = await db.get_user(user_id)
        balance = user["balance"] if user else 0
        await message.answer(
            f"Не хватает баллов 💎\n"
            f"Нужно: <b>{settings.price_energy}</b>, у тебя: <b>{balance}</b>.",
            reply_markup=insufficient_funds_keyboard(),
            parse_mode="HTML",
        )
        return

    number = calc_energy_number(birth, year)
    item = content.energy_year().get(number)
    if not item:
        await message.answer(
            "Не удалось найти описание энергии.",
            reply_markup=back_main(),
        )
        return

    await play_shuffle(message)
    caption = content.format_energy_caption(item, year, number)
    await send_card_result(message, caption, content.major_image_path(number))
    await message.answer("Выбери действие 🍃", reply_markup=back_main())
