import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name, default) or default).strip()


def _env_bool(name: str, default: bool = False) -> bool:
    raw = _env(name, "true" if default else "false").lower()
    return raw in ("1", "true", "yes", "on")


def _env_int(name: str, default: int) -> int:
    try:
        return int(_env(name, str(default)))
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(_env(name, str(default)))
    except ValueError:
        return default


def _parse_admin_ids(raw: str) -> tuple[int, ...]:
    ids: list[int] = []
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if part.isdigit():
            ids.append(int(part))
    return tuple(ids)


def _parse_packs(raw: str) -> dict[str, int]:
    """amount_points:price_rub,..."""
    packs: dict[str, int] = {}
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk or ":" not in chunk:
            continue
        amount, price = chunk.split(":", 1)
        amount, price = amount.strip(), price.strip()
        if amount.isdigit() and price.isdigit():
            packs[amount] = int(price)
    return packs or {"30": 30, "50": 50, "100": 100, "200": 200, "500": 500}


@dataclass(frozen=True)
class Settings:
    bot_token: str = field(default_factory=lambda: _env("BOT_TOKEN"))
    admin_ids: tuple[int, ...] = field(
        default_factory=lambda: _parse_admin_ids(_env("ADMIN_IDS"))
    )
    database_url: str = field(
        default_factory=lambda: _env(
            "DATABASE_URL", "sqlite+aiosqlite:///data_runtime/bot.db"
        )
    )
    price_yes_no: int = field(default_factory=lambda: _env_int("PRICE_YES_NO", 30))
    price_energy: int = field(default_factory=lambda: _env_int("PRICE_ENERGY", 199))
    price_money: int = field(default_factory=lambda: _env_int("PRICE_MONEY", 199))
    start_balance: int = field(default_factory=lambda: _env_int("START_BALANCE", 0))
    enable_stars: bool = field(default_factory=lambda: _env_bool("ENABLE_STARS", True))
    enable_yookassa: bool = field(
        default_factory=lambda: _env_bool("ENABLE_YOOKASSA", True)
    )
    rub_to_stars: float = field(default_factory=lambda: _env_float("RUB_TO_STARS", 1.0))
    yookassa_shop_id: str = field(default_factory=lambda: _env("YOOKASSA_SHOP_ID"))
    yookassa_secret_key: str = field(default_factory=lambda: _env("YOOKASSA_SECRET_KEY"))
    payment_return_url: str = field(
        default_factory=lambda: _env("PAYMENT_RETURN_URL", "https://t.me/")
    )
    balance_packs: dict[str, int] = field(
        default_factory=lambda: _parse_packs(
            _env("BALANCE_PACKS", "30:30,50:50,100:100,200:200,500:500")
        )
    )
    tz: str = field(default_factory=lambda: _env("TZ", "Europe/Moscow"))
    morning_reminder_hour: int = field(
        default_factory=lambda: _env_int("MORNING_REMINDER_HOUR", 10)
    )
    data_dir: Path = field(default_factory=lambda: BASE_DIR / "data")
    pics_dir: Path = field(default_factory=lambda: BASE_DIR / "data" / "pics")
    runtime_dir: Path = field(default_factory=lambda: BASE_DIR / "data_runtime")

    @property
    def balance_packs_stars(self) -> dict[str, int]:
        return {k: max(1, int(v * self.rub_to_stars)) for k, v in self.balance_packs.items()}

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids


settings = Settings()
