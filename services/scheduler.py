from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo

from config import settings
from services.db import db

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone=settings.tz)

REMINDER_TEXT = "🌞 Доброе утро! Твоя карта дня ждёт тебя 🔮"


def reminder_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🃏 Карта дня",
                    callback_data="menu:daycard",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data="goto:menu",
                )
            ],
        ]
    )


async def send_morning_reminders(bot: Bot) -> dict[str, int]:
    """Рассылка напоминаний. Возвращает counts: total/ok/fail."""
    user_ids = await db.users_with_notifications()
    ok = 0
    fail = 0
    kb = reminder_keyboard()
    for tg_id in user_ids:
        try:
            await bot.send_message(tg_id, REMINDER_TEXT, reply_markup=kb)
            ok += 1
        except Exception as exc:
            fail += 1
            # Частые причины: не жали /start, заблокировали бота, удалили чат
            logger.warning("Reminder failed for %s: %s", tg_id, exc)
    logger.info(
        "Morning reminders done: total=%s ok=%s fail=%s",
        len(user_ids),
        ok,
        fail,
    )
    return {"total": len(user_ids), "ok": ok, "fail": fail}


def start_scheduler(bot: Bot) -> None:
    from datetime import datetime

    tz = ZoneInfo(settings.tz)
    scheduler.add_job(
        send_morning_reminders,
        CronTrigger(hour=settings.morning_reminder_hour, minute=0, timezone=tz),
        kwargs={"bot": bot},
        id="morning_reminder",
        replace_existing=True,
    )
    if not scheduler.running:
        scheduler.start()
        now = datetime.now(tz)
        logger.info(
            "Scheduler started: reminder %02d:00 %s | now %s",
            settings.morning_reminder_hour,
            settings.tz,
            now.strftime("%Y-%m-%d %H:%M:%S %Z"),
        )


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
