from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from handlers.day_card import deliver_day_card
from handlers.nav import show_text
from handlers.texts import MAIN_TEXT
from keyboards.main import main_menu
from services.db import db

router = Router()


async def show_main_menu(target: Message | CallbackQuery, *, edit: bool = True) -> None:
    await show_text(target, MAIN_TEXT, main_menu(), edit=edit)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await db.ensure_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
    )
    # Убираем старую reply-клавиатуру, если осталась у пользователя
    cleaner = await message.answer("\u2060", reply_markup=ReplyKeyboardRemove())
    try:
        await cleaner.delete()
    except Exception:
        pass
    await show_main_menu(message, edit=False)
    await deliver_day_card(message, message.from_user.id)


@router.callback_query(F.data == "goto:menu")
async def goto_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await show_main_menu(callback)
