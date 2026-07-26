from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import settings


def balance_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💎 Купить баллы", callback_data="bal:packs")
    )
    builder.row(InlineKeyboardButton(text="📋 История", callback_data="bal:history"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="goto:menu"))
    return builder.as_markup()


def packs_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for points, price in settings.balance_packs.items():
        builder.row(
            InlineKeyboardButton(
                text=f"{points} баллов — {price} ₽",
                callback_data=f"bal:buy:{points}",
            )
        )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="bal:main"))
    return builder.as_markup()


def pay_method_keyboard(points: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if settings.enable_stars:
        stars = settings.balance_packs_stars.get(points)
        if stars is not None:
            builder.row(
                InlineKeyboardButton(
                    text=f"Оплатить Stars ({stars}⭐)",
                    callback_data=f"bal:stars:{points}",
                )
            )
    if (
        settings.enable_yookassa
        and settings.yookassa_shop_id
        and settings.yookassa_secret_key
    ):
        price = settings.balance_packs.get(points)
        builder.row(
            InlineKeyboardButton(
                text=f"Оплатить картой (ЮKassa) — {price}₽",
                callback_data=f"bal:yoo:{points}",
            )
        )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="bal:packs"))
    return builder.as_markup()


def support_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for amount in (50, 100, 300, 500):
        builder.row(
            InlineKeyboardButton(
                text=f"Поддержать на {amount} ₽",
                callback_data=f"support:buy:{amount}",
            )
        )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="goto:other"))
    return builder.as_markup()


def support_method_keyboard(amount: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if settings.enable_stars:
        stars = max(1, int(int(amount) * settings.rub_to_stars))
        builder.row(
            InlineKeyboardButton(
                text=f"Stars ({stars}⭐)",
                callback_data=f"support:stars:{amount}",
            )
        )
    if (
        settings.enable_yookassa
        and settings.yookassa_shop_id
        and settings.yookassa_secret_key
    ):
        builder.row(
            InlineKeyboardButton(
                text=f"Картой (ЮKassa) — {amount}₽",
                callback_data=f"support:yoo:{amount}",
            )
        )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="support:main"))
    return builder.as_markup()
