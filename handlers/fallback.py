from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.fsm.state import default_state
from aiogram.types import Message

from keyboards.main import main_menu

router = Router()


@router.message(StateFilter(default_state))
async def unknown_message(message: Message) -> None:
    """Любой текст/вложение вне сценария (дата, год и т.п.) → главное меню."""
    await message.answer(
        "Выбери действие в меню ниже 🍃",
        reply_markup=main_menu(),
    )
