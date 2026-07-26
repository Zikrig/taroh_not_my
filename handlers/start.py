from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from handlers.day_card import deliver_day_card
from keyboards.main import main_menu
from services.db import db

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await db.ensure_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
    )
    await message.answer(
        "🪳 Привет! Я Аркаша ТАРОкаша!\n\n"
        "Добро пожаловать в мой сказочный лес 🌿✨\n"
        "Выбери действие в меню ниже — или получи карту дня.",
        reply_markup=main_menu(),
    )
    await deliver_day_card(message)


@router.callback_query(F.data == "goto:menu")
async def goto_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    await callback.message.answer("Главное меню 🍃", reply_markup=main_menu())
