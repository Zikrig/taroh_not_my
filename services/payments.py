"""Платежи: YooKassa (рубли) + логика начисления баллов."""

from __future__ import annotations

import logging
import uuid

import httpx
from yookassa import Configuration, Payment

from config import settings

logger = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None


def configure_yookassa() -> bool:
    shop_id = settings.yookassa_shop_id
    secret = settings.yookassa_secret_key
    if not (shop_id and secret):
        return False
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=30.0)
    Configuration.account_id = shop_id
    Configuration.secret_key = secret
    Configuration.configure(
        account_id=shop_id,
        secret_key=secret,
        timeout=30,
        max_attempts=3,
        session=_client,
    )
    return True


async def create_yookassa_payment(
    amount_rub: int,
    description: str,
    email: str = "user@example.com",
) -> dict | None:
    if not settings.enable_yookassa or not configure_yookassa():
        return None
    try:
        payment = Payment.create(
            {
                "amount": {"value": f"{amount_rub:.2f}", "currency": "RUB"},
                "confirmation": {
                    "type": "redirect",
                    "return_url": settings.payment_return_url,
                },
                "capture": True,
                "description": description,
                "receipt": {
                    "customer": {"email": email},
                    "items": [
                        {
                            "description": description[:128],
                            "quantity": "1",
                            "amount": {
                                "value": f"{amount_rub:.2f}",
                                "currency": "RUB",
                            },
                            "vat_code": 1,
                            "payment_mode": "full_prepayment",
                            "payment_subject": "service",
                        }
                    ],
                },
            },
            str(uuid.uuid4()),
        )
        return {
            "id": payment.id,
            "status": payment.status,
            "paid": payment.paid,
            "amount": payment.amount.value,
            "currency": payment.amount.currency,
            "payment_url": payment.confirmation.confirmation_url,
        }
    except Exception:
        logger.exception("YooKassa create_payment failed")
        return None


async def check_yookassa_payment(payment_id: str) -> dict | None:
    if not configure_yookassa():
        return None
    try:
        payment = Payment.find_one(payment_id)
        return {
            "id": payment.id,
            "status": payment.status,
            "paid": payment.paid,
            "amount": payment.amount.value,
            "currency": payment.amount.currency,
        }
    except Exception:
        logger.exception("YooKassa check_payment failed")
        return None
