from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, F, Router
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)

from config import settings
from keyboards.buy import (
    balance_menu,
    packs_keyboard,
    pay_method_keyboard,
    support_method_keyboard,
)
from services.db import db
from services.payments import check_yookassa_payment, create_yookassa_payment

router = Router()
logger = logging.getLogger(__name__)


async def _apply_balance_topup(
    user_id: int,
    points: int,
    charge_id: str | None,
    title: str,
    payload: str,
    notify: Message | Bot,
) -> bool:
    if charge_id and await db.purchase_exists(charge_id):
        if isinstance(notify, Message):
            await notify.answer("Этот платёж уже был обработан ранее.")
        return False

    await db.ensure_user(user_id)
    balance = await db.add_balance(user_id, points)
    await db.add_purchase(user_id, points, payload, title, charge_id)

    text = (
        f"Баланс пополнен на <b>{points}</b> 💎.\n"
        f"Сейчас на счету: <b>{balance}</b> 💎."
    )
    if isinstance(notify, Message):
        await notify.answer(text, parse_mode="HTML")
    else:
        await notify.send_message(user_id, text, parse_mode="HTML")
    return True


async def auto_check_yookassa(
    bot: Bot,
    user_id: int,
    payment_id: str,
    points: int,
    message_id: int,
    chat_id: int,
    amount_rub: int,
) -> None:
    charge_id = f"yookassa-{payment_id}"
    max_checks = 18
    for _ in range(max_checks):
        await asyncio.sleep(30)
        status = await check_yookassa_payment(payment_id)
        if not status:
            continue
        if status.get("paid"):
            if not await db.purchase_exists(charge_id):
                await db.mark_pending_paid(payment_id)
                await _apply_balance_topup(
                    user_id,
                    points,
                    charge_id,
                    f"Пополнение +{points}",
                    f"balance_{points}",
                    bot,
                )
            return

    # финальная проверка
    status = await check_yookassa_payment(payment_id)
    if status and status.get("paid") and not await db.purchase_exists(charge_id):
        await db.mark_pending_paid(payment_id)
        await _apply_balance_topup(
            user_id,
            points,
            charge_id,
            f"Пополнение +{points}",
            f"balance_{points}",
            bot,
        )
        return

    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"Оплата {amount_rub} ₽ не подтверждена. Если уже оплатили — напишите в поддержку.",
        )
    except Exception:
        pass


@router.message(F.text == "💎 Баллы")
async def balance_entry(message: Message) -> None:
    await db.ensure_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
    )
    user = await db.get_user(message.from_user.id)
    balance = user["balance"] if user else 0
    await message.answer(
        f"У тебя на счету <b>{balance}</b> 💎\n"
        "1 балл = 1 ₽.\n\n"
        "Баллы нужны для «Да / Нет», «Энергии года» и «Денежного прогноза».",
        reply_markup=balance_menu(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "bal:main")
async def bal_main(callback: CallbackQuery) -> None:
    await callback.answer()
    user = await db.get_user(callback.from_user.id)
    balance = user["balance"] if user else 0
    await callback.message.answer(
        f"У тебя на счету <b>{balance}</b> 💎",
        reply_markup=balance_menu(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "bal:packs")
async def bal_packs(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        "Выбери пакет баллов:",
        reply_markup=packs_keyboard(),
    )


@router.callback_query(F.data == "bal:history")
async def bal_history(callback: CallbackQuery) -> None:
    await callback.answer()
    rows = await db.recent_purchases(callback.from_user.id)
    if not rows:
        await callback.message.answer("История покупок пуста.")
        return
    lines = []
    for row in rows:
        lines.append(f"{row['created_at'][:16]} — {row['title']} ({row['amount']} 💎)")
    await callback.message.answer("\n".join(lines))


@router.callback_query(F.data.startswith("bal:buy:"))
async def bal_buy(callback: CallbackQuery) -> None:
    await callback.answer()
    points = callback.data.split(":")[-1]
    if points not in settings.balance_packs:
        return
    await callback.message.answer(
        f"Выбери способ оплаты за <b>{points}</b> 💎:",
        reply_markup=pay_method_keyboard(points),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("bal:stars:"))
async def bal_stars(callback: CallbackQuery) -> None:
    await callback.answer()
    points = callback.data.split(":")[-1]
    stars_price = settings.balance_packs_stars.get(points)
    if stars_price is None or not settings.enable_stars:
        return
    await callback.bot.send_invoice(
        chat_id=callback.message.chat.id,
        title=f"Пополнение на {points} 💎",
        description=f"Пополнение баланса на {points} баллов",
        currency="XTR",
        prices=[LabeledPrice(label=f"{points} 💎", amount=int(stars_price))],
        payload=f"balanceStars_{points}",
    )


@router.callback_query(F.data.startswith("bal:yoo:"))
async def bal_yoo(callback: CallbackQuery) -> None:
    await callback.answer()
    points = callback.data.split(":")[-1]
    price = settings.balance_packs.get(points)
    if price is None:
        return
    if not (settings.yookassa_shop_id and settings.yookassa_secret_key):
        await callback.message.answer("Оплата картой временно недоступна.")
        return
    user_id = callback.from_user.id
    pay = await create_yookassa_payment(
        int(price),
        f"Пополнение {points} баллов (User ID: {user_id})",
    )
    if not pay or not pay.get("payment_url"):
        await callback.message.answer("Не удалось создать платёж. Попробуйте Stars или позже.")
        return
    await db.save_pending_payment(pay["id"], user_id, int(points), int(price))
    payment_message = await callback.message.answer(
        f"Оплатите <b>{price}</b> ₽ по ссылке:\n{pay['payment_url']}",
        parse_mode="HTML",
    )
    asyncio.create_task(
        auto_check_yookassa(
            callback.bot,
            user_id,
            pay["id"],
            int(points),
            payment_message.message_id,
            payment_message.chat.id,
            int(price),
        )
    )


@router.callback_query(F.data.startswith("support:buy:"))
async def support_buy(callback: CallbackQuery) -> None:
    await callback.answer()
    amount = callback.data.split(":")[-1]
    await callback.message.answer(
        f"Способ поддержки на <b>{amount}</b> ₽:",
        reply_markup=support_method_keyboard(amount),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("support:stars:"))
async def support_stars(callback: CallbackQuery) -> None:
    await callback.answer()
    amount = callback.data.split(":")[-1]
    if not settings.enable_stars:
        return
    stars = max(1, int(int(amount) * settings.rub_to_stars))
    await callback.bot.send_invoice(
        chat_id=callback.message.chat.id,
        title="Поддержка автора",
        description=f"Добровольная поддержка на {amount} ₽",
        currency="XTR",
        prices=[LabeledPrice(label="Поддержка", amount=stars)],
        payload=f"supportStars_{amount}",
    )


@router.callback_query(F.data.startswith("support:yoo:"))
async def support_yoo(callback: CallbackQuery) -> None:
    await callback.answer()
    amount = callback.data.split(":")[-1]
    if not (settings.yookassa_shop_id and settings.yookassa_secret_key):
        await callback.message.answer("Оплата картой временно недоступна.")
        return
    user_id = callback.from_user.id
    pay = await create_yookassa_payment(
        int(amount),
        f"Поддержка автора (User ID: {user_id})",
    )
    if not pay or not pay.get("payment_url"):
        await callback.message.answer("Не удалось создать платёж.")
        return
    # поддержка = те же баллы, чтобы пользователь получил ценность
    await db.save_pending_payment(pay["id"], user_id, int(amount), int(amount))
    payment_message = await callback.message.answer(
        f"Оплатите <b>{amount}</b> ₽ по ссылке:\n{pay['payment_url']}\n\n"
        f"После оплаты на баланс придёт <b>{amount}</b> 💎.",
        parse_mode="HTML",
    )
    asyncio.create_task(
        auto_check_yookassa(
            callback.bot,
            user_id,
            pay["id"],
            int(amount),
            payment_message.message_id,
            payment_message.chat.id,
            int(amount),
        )
    )


@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery) -> None:
    await pre_checkout_query.bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@router.message(F.successful_payment)
async def on_successful_payment(message: Message) -> None:
    payload = message.successful_payment.invoice_payload
    charge_id = getattr(message.successful_payment, "telegram_payment_charge_id", None)
    user_id = message.from_user.id

    if payload.startswith("balanceStars_"):
        points = int(payload.split("_", 1)[1])
        await _apply_balance_topup(
            user_id,
            points,
            charge_id,
            f"Пополнение Stars +{points}",
            payload,
            message,
        )
    elif payload.startswith("supportStars_"):
        amount = int(payload.split("_", 1)[1])
        await _apply_balance_topup(
            user_id,
            amount,
            charge_id,
            f"Поддержка +{amount}",
            payload,
            message,
        )
        await message.answer("Спасибо за поддержку автора! 🩷✨")
    else:
        await message.answer("Платёж получен. Если баллы не начислились — напишите в поддержку.")
