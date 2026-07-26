from __future__ import annotations

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message


async def show_text(
    target: Message | CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    *,
    edit: bool = True,
) -> Message:
    """Показать экран: edit у callback, иначе новое сообщение."""
    if isinstance(target, CallbackQuery):
        await target.answer()
        message = target.message
        if edit and message and not message.photo and not message.video:
            try:
                return await message.edit_text(
                    text, reply_markup=reply_markup, parse_mode="HTML"
                )
            except TelegramBadRequest:
                pass
        return await message.answer(
            text, reply_markup=reply_markup, parse_mode="HTML"
        )
    return await target.answer(text, reply_markup=reply_markup, parse_mode="HTML")
