from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import settings
from handlers.common import today_key
from services.db import db

router = Router()


@router.message(Command("stats"))
async def stats(message: Message) -> None:
    if not settings.is_admin(message.from_user.id):
        return
    total = await db.count_users()
    today = await db.count_day_cards(today_key())
    await message.answer(
        f"📊 <b>Статистика</b>\n\n"
        f"Всего пользователей: <b>{total}</b>\n"
        f"Карта дня за сегодня: <b>{today}</b>",
        parse_mode="HTML",
    )


@router.message(Command("add_points"))
async def add_points(message: Message) -> None:
    """ /add_points <tg_id> <amount> """
    if not settings.is_admin(message.from_user.id):
        return
    parts = (message.text or "").split()
    if len(parts) != 3 or not parts[1].isdigit() or not parts[2].lstrip("-").isdigit():
        await message.answer("Формат: <code>/add_points tg_id amount</code>", parse_mode="HTML")
        return
    tg_id, amount = int(parts[1]), int(parts[2])
    await db.ensure_user(tg_id)
    balance = await db.add_balance(tg_id, amount)
    await message.answer(f"Готово. Баланс {tg_id}: <b>{balance}</b> 💎", parse_mode="HTML")
