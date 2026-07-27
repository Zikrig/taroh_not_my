from aiogram import F, Router
from aiogram.filters import CommandStart, CommandObject
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


async def _clear_reply_keyboard(message: Message) -> None:
    cleaner = await message.answer("\u2060", reply_markup=ReplyKeyboardRemove())
    try:
        await cleaner.delete()
    except Exception:
        pass


@router.message(CommandStart())
async def cmd_start(
    message: Message, state: FSMContext, command: CommandObject
) -> None:
    await state.clear()
    await db.ensure_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
    )
    await _clear_reply_keyboard(message)

    # Из напоминания: /start daycard — сразу карта без длинного текста
    args = (command.args or "").strip().lower()
    if args in {"daycard", "card", "day"}:
        await deliver_day_card(message, message.from_user.id)
        return

    await show_main_menu(message, edit=False)


@router.callback_query(F.data == "goto:menu")
async def goto_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await show_main_menu(callback)
