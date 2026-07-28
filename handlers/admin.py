from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import settings
from handlers.common import today_key
from services.db import db
from services.scheduler import send_morning_reminders

router = Router()


@router.message(Command("stats"))
async def stats(message: Message) -> None:
    if not settings.is_admin(message.from_user.id):
        return
    total = await db.count_users()
    today = await db.count_day_cards(today_key())
    notify = len(await db.users_with_notifications())
    await message.answer(
        f"📊 <b>Статистика</b>\n\n"
        f"Всего пользователей: <b>{total}</b>\n"
        f"С напоминаниями: <b>{notify}</b>\n"
        f"Карта дня за сегодня: <b>{today}</b>",
        parse_mode="HTML",
    )


@router.message(Command("users"))
async def list_users(message: Message) -> None:
    """Список пользователей (кто в базе и получит напоминание)."""
    if not settings.is_admin(message.from_user.id):
        return
    rows = await db.list_users(limit=50)
    if not rows:
        await message.answer("Пользователей пока нет.")
        return
    lines = ["👥 <b>Пользователи</b> (до 50):\n"]
    for u in rows:
        name = u.get("full_name") or "—"
        uname = f"@{u['username']}" if u.get("username") else "—"
        flag = "✅" if u.get("notifications") else "🔕"
        lines.append(
            f"{flag} <code>{u['tg_id']}</code> · {name} · {uname}"
        )
    lines.append(
        "\nНапоминание уходит в 10:00 МСК всем с ✅, "
        "кто уже нажал /start до этого времени."
    )
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("remind_now"))
async def remind_now(message: Message) -> None:
    """Сразу разослать утреннее напоминание всем (тест)."""
    if not settings.is_admin(message.from_user.id):
        return
    await message.answer("Рассылаю напоминания…")
    result = await send_morning_reminders(message.bot)
    await message.answer(
        f"Готово.\n"
        f"Всего: <b>{result['total']}</b>\n"
        f"Доставлено: <b>{result['ok']}</b>\n"
        f"Ошибки: <b>{result['fail']}</b>\n\n"
        f"Если fail &gt; 0 — смотри логи: пользователь не жали /start "
        f"или заблокировал бота.",
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
