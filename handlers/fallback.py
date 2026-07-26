from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.fsm.state import default_state
from aiogram.types import Message

from handlers.texts import MAIN_TEXT
from keyboards.main import main_menu

router = Router()


@router.message(StateFilter(default_state))
async def unknown_message(message: Message) -> None:
    """Любое сообщение вне сценария → главное меню с инлайн-кнопками."""
    await message.answer(MAIN_TEXT, reply_markup=main_menu())
