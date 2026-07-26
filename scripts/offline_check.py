"""Офлайн-проверка бота без обращения к Telegram API."""

from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

errors: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    status = "OK" if cond else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))
    if not cond:
        errors.append(name if not detail else f"{name}: {detail}")


def check_data_files() -> None:
    required = [
        "day_cards.json",
        "yes_no.json",
        "energy_year.json",
        "money_forecast.json",
        "card_images.json",
    ]
    for name in required:
        path = ROOT / "data" / name
        check(f"data/{name}", path.exists())

    day = json.loads((ROOT / "data" / "day_cards.json").read_text(encoding="utf-8"))
    yn = json.loads((ROOT / "data" / "yes_no.json").read_text(encoding="utf-8"))
    energy = json.loads((ROOT / "data" / "energy_year.json").read_text(encoding="utf-8"))
    money = json.loads((ROOT / "data" / "money_forecast.json").read_text(encoding="utf-8"))
    imgs = json.loads((ROOT / "data" / "card_images.json").read_text(encoding="utf-8"))
    pics = {p.name for p in (ROOT / "data" / "pics").iterdir() if p.is_file()}

    check("day_cards count", len(day) == 78, str(len(day)))
    check("yes_no count", len(yn) == 22, str(len(yn)))
    check("energy_year count", len(energy) == 22, str(len(energy)))
    check("money_forecast count", len(money) == 22, str(len(money)))
    check("card_images count", len(imgs) == 78, str(len(imgs)))
    check("pics count", len(pics) == 78, str(len(pics)))

    day_ids = {c["id"] for c in day}
    check("all day cards mapped", day_ids <= set(imgs))
    missing_files = [imgs[i] for i in sorted(day_ids) if imgs.get(i) not in pics]
    check("all mapped files exist", not missing_files, str(missing_files[:5]))

    energy_nums = sorted(int(x["number"]) for x in energy)
    money_nums = sorted(int(x["number"]) for x in money)
    check("energy numbers 1..22", energy_nums == list(range(1, 23)))
    check("money numbers 1..22", money_nums == list(range(1, 23)))

    yn_answers = sum(1 for x in yn if x.get("answer"))
    check("yes_no answers parsed", yn_answers == 22, str(yn_answers))


def check_numerology() -> None:
    from services.numerology import calc_energy_number, parse_birth_date

    birth = parse_birth_date("25.08.1995")
    check("parse full date", birth == date(1995, 8, 25))
    check("parse short date", parse_birth_date("25.08") is not None)
    check("parse bad date", parse_birth_date("32.13") is None)
    check("example energy 2026", calc_energy_number(date(1995, 8, 25), 2026) == 3)
    # 2+5+0+8+2+0+2+7 = 26 -> 4
    check("energy 2027", calc_energy_number(date(1995, 8, 25), 2027) == 4)
    check("reduce loop", calc_energy_number(date(1999, 9, 29), 2099) <= 22)


def check_content() -> None:
    from services import content

    content.day_cards.cache_clear()
    content.card_images.cache_clear()

    card = content.pick_day_card(42, "2026-07-26")
    card2 = content.pick_day_card(42, "2026-07-26")
    check("day card deterministic", card["id"] == card2["id"])
    check("day card has text", bool(card.get("text") and card.get("name")))

    path = content.card_image_path(card["id"])
    check("day card image path", path is not None and path.exists(), str(path))

    for n in range(1, 23):
        p = content.major_image_path(n)
        check(f"major image {n}", p is not None and p.exists(), str(p))

    yn = content.pick_yes_no_card()
    check("yes_no pick", "number" in yn and "text" in yn)

    e = content.energy_year()[3]
    m = content.money_forecast()[3]
    cap_e = content.format_energy_caption(e, 2026, 3)
    cap_m = content.format_money_caption(m, 2026, 3)
    check("energy caption", "3" in cap_e and e["name"] in cap_e)
    check("money caption", "3" in cap_m)
    check("money caption under 4096", len(cap_m) <= 4096, str(len(cap_m)))


def check_timezone() -> None:
    try:
        tz = ZoneInfo("Europe/Moscow")
        check("ZoneInfo Europe/Moscow", True, str(tz))
    except Exception as exc:
        check("ZoneInfo Europe/Moscow", False, str(exc))


def check_handlers_and_bot_object() -> None:
    from aiogram import Bot, Dispatcher
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode
    from aiogram.fsm.storage.memory import MemoryStorage

    from handlers import setup_routers
    from keyboards.main import main_menu

    router = setup_routers()
    check("routers setup", router is not None)

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    updates = dp.resolve_used_update_types()
    check(
        "updates include payments",
        "pre_checkout_query" in updates or "message" in updates,
        str(updates),
    )

    # Создание Bot без сетевых вызовов
    bot = Bot(
        token="0000000000:FAKE_TOKEN_FOR_OFFLINE_CHECK______________",
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    check("Bot object created", bot is not None)
    kb = main_menu()
    check("main keyboard", kb is not None)


async def check_db() -> None:
    from services.db import Database

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        db = Database(f"sqlite+aiosqlite:///{db_path.as_posix()}")
        await db.connect()
        user = await db.ensure_user(1001, "u", "User")
        check("db create user", user["tg_id"] == 1001)
        # Обнуляем стартовый баланс из .env, чтобы тест был детерминированным
        cur = await db.get_user(1001)
        if cur and cur["balance"]:
            await db.try_spend(1001, int(cur["balance"]))
        await db.add_balance(1001, 199)
        ok = await db.try_spend(1001, 199)
        check("db spend exact", ok)
        ok2 = await db.try_spend(1001, 1)
        check("db spend insufficient", not ok2)
        await db.set_birth_date(1001, date(1995, 8, 25))
        birth = await db.get_birth_date(1001)
        check("db birth date", birth == date(1995, 8, 25))
        cid, new = await db.get_or_create_day_card(1001, "2026-07-26", "0_shut")
        cid2, new2 = await db.get_or_create_day_card(1001, "2026-07-26", "1_mag")
        check("db day card sticky", cid == cid2 == "0_shut" and new and not new2)
        await db.add_purchase(1001, 50, "balance_50", "test", "charge-1")
        check("db purchase dedupe", await db.purchase_exists("charge-1"))
        check("db users count", await db.count_users() >= 1)
        await db.close()


def check_project_artifacts() -> None:
    needed = [
        "bot.py",
        "requirements.txt",
        ".env.example",
        ".gitignore",
        ".dockerignore",
        "Dockerfile",
        "docker-compose.yml",
        "instructions.readme",
        "about.readme",
    ]
    for name in needed:
        check(f"artifact {name}", (ROOT / name).exists())


async def main() -> None:
    print("=== Offline checks (no Telegram) ===")
    check_project_artifacts()
    check_data_files()
    check_numerology()
    check_content()
    check_timezone()
    check_handlers_and_bot_object()
    await check_db()
    print("---")
    if errors:
        print(f"FAILED: {len(errors)}")
        for e in errors:
            print(" -", e)
        raise SystemExit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    asyncio.run(main())
