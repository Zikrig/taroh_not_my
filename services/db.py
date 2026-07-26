from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import aiosqlite

from config import settings

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _sqlite_path(database_url: str) -> Path:
    # sqlite+aiosqlite:///data_runtime/bot.db  or  sqlite:///...
    url = database_url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    if url.startswith("sqlite:///"):
        raw = url[len("sqlite:///") :]
    else:
        parsed = urlparse(url)
        raw = unquote(parsed.path.lstrip("/"))
    path = Path(raw)
    if not path.is_absolute():
        path = PROJECT_ROOT / raw
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


class Database:
    def __init__(self, database_url: str | None = None) -> None:
        self.path = _sqlite_path(database_url or settings.database_url)
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self.path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA foreign_keys = ON")
        await self._init_schema()

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if not self._conn:
            raise RuntimeError("Database is not connected")
        return self._conn

    async def _init_schema(self) -> None:
        await self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                tg_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                balance INTEGER NOT NULL DEFAULT 0,
                birth_day INTEGER,
                birth_month INTEGER,
                birth_year INTEGER,
                notifications INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS day_cards (
                tg_id INTEGER NOT NULL,
                day_key TEXT NOT NULL,
                card_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (tg_id, day_key)
            );

            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                payload TEXT,
                title TEXT,
                charge_id TEXT UNIQUE,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS pending_payments (
                payment_id TEXT PRIMARY KEY,
                tg_id INTEGER NOT NULL,
                points INTEGER NOT NULL,
                amount_rub INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending'
            );

            CREATE INDEX IF NOT EXISTS idx_day_cards_day ON day_cards(day_key);
            CREATE INDEX IF NOT EXISTS idx_purchases_tg ON purchases(tg_id);
            """
        )
        await self.conn.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    async def ensure_user(
        self,
        tg_id: int,
        username: str | None = None,
        full_name: str | None = None,
    ) -> dict[str, Any]:
        row = await self.get_user(tg_id)
        now = self._now()
        if row:
            await self.conn.execute(
                """
                UPDATE users
                SET username = ?, full_name = ?, updated_at = ?
                WHERE tg_id = ?
                """,
                (username, full_name, now, tg_id),
            )
            await self.conn.commit()
            return await self.get_user(tg_id)  # type: ignore[return-value]

        await self.conn.execute(
            """
            INSERT INTO users (tg_id, username, full_name, balance, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (tg_id, username, full_name, settings.start_balance, now, now),
        )
        await self.conn.commit()
        return await self.get_user(tg_id)  # type: ignore[return-value]

    async def get_user(self, tg_id: int) -> dict[str, Any] | None:
        cur = await self.conn.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

    async def set_birth_date(self, tg_id: int, birth: date) -> None:
        await self.conn.execute(
            """
            UPDATE users
            SET birth_day = ?, birth_month = ?, birth_year = ?, updated_at = ?
            WHERE tg_id = ?
            """,
            (birth.day, birth.month, birth.year, self._now(), tg_id),
        )
        await self.conn.commit()

    async def get_birth_date(self, tg_id: int) -> date | None:
        user = await self.get_user(tg_id)
        if not user or not user.get("birth_day") or not user.get("birth_month"):
            return None
        year = user.get("birth_year") or 2000
        try:
            return date(int(year), int(user["birth_month"]), int(user["birth_day"]))
        except ValueError:
            return None

    async def add_balance(self, tg_id: int, amount: int) -> int:
        await self.conn.execute(
            """
            UPDATE users
            SET balance = balance + ?, updated_at = ?
            WHERE tg_id = ?
            """,
            (amount, self._now(), tg_id),
        )
        await self.conn.commit()
        user = await self.get_user(tg_id)
        return int(user["balance"]) if user else 0

    async def try_spend(self, tg_id: int, amount: int) -> bool:
        cur = await self.conn.execute(
            """
            UPDATE users
            SET balance = balance - ?, updated_at = ?
            WHERE tg_id = ? AND balance >= ?
            """,
            (amount, self._now(), tg_id, amount),
        )
        await self.conn.commit()
        return cur.rowcount > 0

    async def get_or_create_day_card(
        self, tg_id: int, day_key: str, card_id: str
    ) -> tuple[str, bool]:
        """Возвращает (card_id, is_new)."""
        cur = await self.conn.execute(
            "SELECT card_id FROM day_cards WHERE tg_id = ? AND day_key = ?",
            (tg_id, day_key),
        )
        row = await cur.fetchone()
        if row:
            return row["card_id"], False
        await self.conn.execute(
            """
            INSERT INTO day_cards (tg_id, day_key, card_id, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (tg_id, day_key, card_id, self._now()),
        )
        await self.conn.commit()
        return card_id, True

    async def count_users(self) -> int:
        cur = await self.conn.execute("SELECT COUNT(*) AS c FROM users")
        row = await cur.fetchone()
        return int(row["c"]) if row else 0

    async def count_day_cards(self, day_key: str) -> int:
        cur = await self.conn.execute(
            "SELECT COUNT(*) AS c FROM day_cards WHERE day_key = ?",
            (day_key,),
        )
        row = await cur.fetchone()
        return int(row["c"]) if row else 0

    async def users_with_notifications(self) -> list[int]:
        cur = await self.conn.execute(
            "SELECT tg_id FROM users WHERE notifications = 1"
        )
        rows = await cur.fetchall()
        return [int(r["tg_id"]) for r in rows]

    async def purchase_exists(self, charge_id: str) -> bool:
        cur = await self.conn.execute(
            "SELECT 1 FROM purchases WHERE charge_id = ?",
            (charge_id,),
        )
        return await cur.fetchone() is not None

    async def add_purchase(
        self,
        tg_id: int,
        amount: int,
        payload: str,
        title: str,
        charge_id: str | None,
    ) -> None:
        await self.conn.execute(
            """
            INSERT INTO purchases (tg_id, amount, payload, title, charge_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (tg_id, amount, payload, title, charge_id, self._now()),
        )
        await self.conn.commit()

    async def save_pending_payment(
        self, payment_id: str, tg_id: int, points: int, amount_rub: int
    ) -> None:
        await self.conn.execute(
            """
            INSERT OR REPLACE INTO pending_payments
            (payment_id, tg_id, points, amount_rub, created_at, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
            """,
            (payment_id, tg_id, points, amount_rub, self._now()),
        )
        await self.conn.commit()

    async def get_pending_payment(self, payment_id: str) -> dict[str, Any] | None:
        cur = await self.conn.execute(
            "SELECT * FROM pending_payments WHERE payment_id = ?",
            (payment_id,),
        )
        row = await cur.fetchone()
        return dict(row) if row else None

    async def mark_pending_paid(self, payment_id: str) -> None:
        await self.conn.execute(
            "UPDATE pending_payments SET status = 'paid' WHERE payment_id = ?",
            (payment_id,),
        )
        await self.conn.commit()

    async def count_purchases(self, tg_id: int) -> int:
        cur = await self.conn.execute(
            "SELECT COUNT(*) AS c FROM purchases WHERE tg_id = ?",
            (tg_id,),
        )
        row = await cur.fetchone()
        return int(row["c"]) if row else 0

    async def recent_purchases(
        self, tg_id: int, limit: int = 10, offset: int = 0
    ) -> list[dict[str, Any]]:
        cur = await self.conn.execute(
            """
            SELECT amount, payload, title, charge_id, created_at
            FROM purchases
            WHERE tg_id = ?
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (tg_id, limit, offset),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


db = Database()
