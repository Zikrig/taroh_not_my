"""Проверка ключей ЮKassa из .env.

Запуск локально:
  python scripts/test_yookassa.py

На сервере в Docker:
  docker compose exec bot python scripts/test_yookassa.py

С созданием тестового платежа на 1 ₽ (не оплачивать):
  python scripts/test_yookassa.py --create
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import httpx  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from config import settings  # noqa: E402


def _mask(value: str, keep: int = 4) -> str:
    if not value:
        return "(пусто)"
    if len(value) <= keep * 2:
        return "*" * len(value)
    return f"{value[:keep]}…{value[-keep:]} (len={len(value)})"


def check_credentials() -> int:
    shop_id = settings.yookassa_shop_id
    secret = settings.yookassa_secret_key

    print("=== YooKassa credentials ===")
    print(f"ENABLE_YOOKASSA : {settings.enable_yookassa}")
    print(f"YOOKASSA_SHOP_ID: {_mask(shop_id, keep=2)}")
    print(f"SECRET_KEY      : {_mask(secret, keep=6)}")
    print(f"RETURN_URL      : {settings.payment_return_url or '(пусто)'}")
    print()

    if not shop_id or not secret:
        print("FAIL: shopId или secret key не заданы в .env")
        return 1

    url = "https://api.yookassa.ru/v3/payments"
    try:
        resp = httpx.get(
            url,
            params={"limit": 1},
            auth=(shop_id, secret),
            timeout=30.0,
        )
    except httpx.HTTPError as exc:
        print(f"FAIL: сеть — {exc}")
        return 1

    print(f"GET {url} -> HTTP {resp.status_code}")
    if resp.status_code == 200:
        print("OK: ключи приняты, доступ к API есть")
        return 0

    print(f"Body: {resp.text[:500]}")
    if resp.status_code == 401:
        print(
            "FAIL: invalid_credentials — проверь shopId и secret key "
            "(тест/бой, пробелы, кавычки в .env)"
        )
    else:
        print("FAIL: неожиданный ответ API")
    return 1


def create_test_payment() -> int:
    from yookassa import Configuration, Payment
    import uuid

    shop_id = settings.yookassa_shop_id
    secret = settings.yookassa_secret_key
    if not shop_id or not secret:
        print("FAIL: нет ключей")
        return 1

    Configuration.account_id = shop_id
    Configuration.secret_key = secret

    try:
        payment = Payment.create(
            {
                "amount": {"value": "1.00", "currency": "RUB"},
                "confirmation": {
                    "type": "redirect",
                    "return_url": settings.payment_return_url or "https://t.me/",
                },
                "capture": True,
                "description": "Тест подключения ТАРО-бота",
            },
            str(uuid.uuid4()),
        )
    except Exception as exc:
        print(f"FAIL: create payment — {exc}")
        return 1

    print("OK: тестовый платёж создан (1 ₽, можно не оплачивать)")
    print(f"  id:     {payment.id}")
    print(f"  status: {payment.status}")
    conf = getattr(payment, "confirmation", None)
    url = getattr(conf, "confirmation_url", None) if conf else None
    if url:
        print(f"  url:    {url}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Проверка ЮKassa")
    parser.add_argument(
        "--create",
        action="store_true",
        help="Создать тестовый платёж на 1 ₽",
    )
    args = parser.parse_args()

    code = check_credentials()
    if code != 0 or not args.create:
        return code
    print()
    return create_test_payment()


if __name__ == "__main__":
    raise SystemExit(main())
