from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import settings


def balance_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💎 Купить баллы", callback_data="bal:packs")
    )
    builder.row(InlineKeyboardButton(text="📋 История", callback_data="bal:history:0"))
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


HISTORY_PAGE_SIZE = 10


def _is_stars_purchase(row: dict) -> bool:
    payload = row.get("payload") or ""
    title = row.get("title") or ""
    charge = row.get("charge_id") or ""
    if charge.startswith("yookassa-"):
        return False
    return (
        payload.startswith("balanceStars")
        or payload.startswith("supportStars")
        or "Stars" in title
    )


def format_history_label(row: dict, tz_name: str = "Europe/Moscow") -> str:
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo

    raw = row.get("created_at") or ""
    try:
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt = dt.astimezone(ZoneInfo(tz_name))
        when = dt.strftime("%H:%M %d.%m.%Y")
    except Exception:
        when = str(raw)[:16]

    amount = int(row.get("amount") or 0)
    kind = "Stars" if _is_stars_purchase(row) else "р"
    # Лимит текста кнопки Telegram — 64 символа
    label = f"{when}   {kind} +{amount} 💎"
    return label[:64]


def history_keyboard(
    rows: list[dict],
    page: int,
    total: int,
    *,
    tz_name: str = "Europe/Moscow",
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, row in enumerate(rows):
        builder.row(
            InlineKeyboardButton(
                text=format_history_label(row, tz_name),
                callback_data=f"bal:hist:item:{page}:{i}",
            )
        )

    page_size = HISTORY_PAGE_SIZE
    pages = max(1, (total + page_size - 1) // page_size)
    if pages > 1:
        nav: list[InlineKeyboardButton] = []
        if page > 0:
            nav.append(
                InlineKeyboardButton(
                    text="‹", callback_data=f"bal:history:{page - 1}"
                )
            )
        nav.append(
            InlineKeyboardButton(
                text=f"{page + 1}/{pages}", callback_data="bal:hist:noop"
            )
        )
        if page + 1 < pages:
            nav.append(
                InlineKeyboardButton(
                    text="›", callback_data=f"bal:history:{page + 1}"
                )
            )
        builder.row(*nav)

    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="bal:main"))
    return builder.as_markup()
