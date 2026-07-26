from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from handlers.energy import show_energy
from handlers.money import show_money
from handlers.nav import show_text
from handlers.states import ProfileStates
from handlers.texts import ABOUT_SHORT, AGREEMENT, OTHER_TEXT, SUPPORT
from keyboards.buy import support_keyboard
from keyboards.main import back_other, cancel_input_keyboard, other_menu
from services.db import db
from services.numerology import parse_birth_date

router = Router()


@router.callback_query(F.data == "goto:other")
async def goto_other(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await show_text(callback, OTHER_TEXT, other_menu())


@router.callback_query(F.data == "other:about")
async def other_about(callback: CallbackQuery) -> None:
    await show_text(callback, ABOUT_SHORT, back_other())


@router.callback_query(F.data == "other:agreement")
async def other_agreement(callback: CallbackQuery) -> None:
    await show_text(callback, AGREEMENT, back_other())


@router.callback_query(F.data == "support:main")
async def support_main(callback: CallbackQuery) -> None:
    await show_text(callback, SUPPORT, support_keyboard())


@router.callback_query(F.data == "other:set_birth")
async def ask_birth(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    # Откуда пришли — чтобы вернуть после сохранения
    # message с кнопкой из energy/money содержит характерный текст
    text = (callback.message.text or "") if callback.message else ""
    if "Энергия года" in text or "энергия будет сопровождать" in text:
        return_to = "energy"
    elif "Денежный прогноз" in text or "финансового изобилия" in text:
        return_to = "money"
    else:
        return_to = "other"
    await state.set_state(ProfileStates.waiting_birth)
    await state.update_data(return_to=return_to)
    birth = await db.get_birth_date(callback.from_user.id)
    current = (
        f"Сейчас сохранено: <b>{birth.strftime('%d.%m.%Y')}</b>\n\n" if birth else ""
    )
    back_cb = f"goto:{return_to}" if return_to != "other" else "goto:other"
    await callback.message.answer(
        f"{current}"
        "Напиши дату рождения в формате <b>ДД.ММ.ГГГГ</b> или <b>ДД.ММ</b>\n"
        "Например: <code>25.08.1995</code> или <code>25.08</code>",
        reply_markup=cancel_input_keyboard(back_cb),
        parse_mode="HTML",
    )


@router.message(ProfileStates.waiting_birth)
async def save_birth(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    return_to = data.get("return_to", "other")
    birth = parse_birth_date(message.text or "")
    if not birth:
        back_cb = f"goto:{return_to}" if return_to != "other" else "goto:other"
        await message.answer(
            "Не получилось распознать дату. Пример: <code>25.08.1995</code>",
            reply_markup=cancel_input_keyboard(back_cb),
            parse_mode="HTML",
        )
        return
    await db.ensure_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
    )
    await db.set_birth_date(message.from_user.id, birth)
    await state.clear()
    await message.answer(
        f"Сохранила дату: <b>{birth.strftime('%d.%m.%Y')}</b> 🍀",
        parse_mode="HTML",
    )
    if return_to == "energy":
        await show_energy(
            message,
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name,
        )
    elif return_to == "money":
        await show_money(
            message,
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name,
        )
    else:
        await message.answer(OTHER_TEXT, reply_markup=other_menu(), parse_mode="HTML")
