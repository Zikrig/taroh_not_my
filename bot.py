import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNetworkError
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from handlers import setup_routers
from services import content
from services.db import db
from services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


def _self_check() -> None:
    """Локальные проверки до polling — без запросов к Telegram."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    cards = content.day_cards()
    images = content.card_images()
    if len(cards) != 78:
        raise SystemExit(f"Expected 78 day cards, got {len(cards)}")
    if len(images) != 78:
        raise SystemExit(f"Expected 78 card images map, got {len(images)}")
    missing = [
        cid
        for cid in (c["id"] for c in cards)
        if not (settings.pics_dir / images.get(cid, "")).exists()
    ]
    if missing:
        raise SystemExit(f"Missing image files for: {missing[:5]}")
    for name in ("yes_no.json", "energy_year.json", "money_forecast.json"):
        if not (settings.data_dir / name).exists():
            raise SystemExit(f"Missing data file: {name}")
    try:
        tz = ZoneInfo(settings.tz)
    except Exception as exc:
        raise SystemExit(f"Invalid TZ={settings.tz!r}: {exc}") from exc
    now = datetime.now(tz)
    logger.info(
        "Self-check OK: 78 cards | TZ=%s | now=%s",
        settings.tz,
        now.strftime("%Y-%m-%d %H:%M:%S %Z"),
    )


async def main() -> None:
    if not settings.bot_token:
        raise SystemExit("BOT_TOKEN is not set in .env")

    _self_check()
    await db.connect()
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(setup_routers())

    start_scheduler(bot)
    logger.info("Bot starting…")
    try:
        while True:
            try:
                await dp.start_polling(
                    bot, allowed_updates=dp.resolve_used_update_types()
                )
                break
            except TelegramNetworkError as exc:
                logger.warning("Telegram network error: %s. Retry in 5s…", exc)
                await asyncio.sleep(5)
    finally:
        stop_scheduler()
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
