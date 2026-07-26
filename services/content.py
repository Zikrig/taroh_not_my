from __future__ import annotations

import json
import random
from functools import lru_cache
from pathlib import Path

from config import settings

MAJOR_IMAGE_KEYS = {
    0: "0_shut",
    1: "1_mag",
    2: "2_zhritsa",
    3: "3_imperatritsa",
    4: "4_imperator",
    5: "5_ierofant",
    6: "6_vlyublennye",
    7: "7_kolesnitsa",
    8: "8_sila",
    9: "9_otshelnik",
    10: "10_koleso",
    11: "11_spravedlivost",
    12: "12_poveshennyy",
    13: "13_smert",
    14: "14_umerennost",
    15: "15_dyavol",
    16: "16_bashnya",
    17: "17_zvezda",
    18: "18_luna",
    19: "19_solntse",
    20: "20_sud",
    21: "21_mir",
    22: "0_shut",
}


def _load_json(name: str):
    path = settings.data_dir / name
    with path.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def day_cards() -> list[dict]:
    return _load_json("day_cards.json")


@lru_cache(maxsize=1)
def yes_no_cards() -> list[dict]:
    return _load_json("yes_no.json")


@lru_cache(maxsize=1)
def energy_year() -> dict[int, dict]:
    items = _load_json("energy_year.json")
    return {int(item["number"]): item for item in items}


@lru_cache(maxsize=1)
def money_forecast() -> dict[int, dict]:
    items = _load_json("money_forecast.json")
    return {int(item["number"]): item for item in items}


@lru_cache(maxsize=1)
def card_images() -> dict[str, str]:
    path = settings.data_dir / "card_images.json"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def card_image_path(card_id: str) -> Path | None:
    filename = card_images().get(card_id)
    if not filename:
        return None
    path = settings.pics_dir / filename
    return path if path.exists() else None


def major_image_path(number: int) -> Path | None:
    key = MAJOR_IMAGE_KEYS.get(number)
    if not key:
        return None
    return card_image_path(key)


def pick_day_card(user_id: int, day_key: str) -> dict:
    """Детерминированная карта дня на пользователя + дату."""
    cards = day_cards()
    rng = random.Random(f"{user_id}:{day_key}")
    return rng.choice(cards)


def pick_yes_no_card() -> dict:
    return random.choice(yes_no_cards())


def format_day_card_caption(card: dict) -> str:
    name = card["name"]
    text = card["text"]
    advice = card.get("advice") or ""
    lines = [f"<b>{name}</b>", "", text]
    if advice:
        lines.extend(["", f"<b>Совет:</b> {advice}"])
    return "\n".join(lines)


def format_yes_no_caption(card: dict) -> str:
    name = card["name"]
    answer = (card.get("answer") or "").strip()
    text = card["text"]
    head = f"<b>{name}</b>"
    if answer:
        head += f"\n<b>{answer}</b>"
    return f"{head}\n\n{text}"


def format_energy_caption(item: dict, year: int, number: int) -> str:
    return (
        f"✨ <b>Твоя Энергия года {year} — {number}. {item['name']}</b>\n\n"
        f"{item['text']}"
    )


def format_money_caption(item: dict, year: int, number: int) -> str:
    return (
        f"💰 <b>Денежный прогноз на {year} — {number}. {item['name']}</b>\n\n"
        f"{item['text']}"
    )
