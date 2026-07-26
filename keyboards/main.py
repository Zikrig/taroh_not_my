from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def main_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="🃏 Карта дня"))
    builder.row(
        KeyboardButton(text="✅ Да / Нет"),
        KeyboardButton(text="🍀 Энергия года"),
    )
    builder.row(
        KeyboardButton(text="💰 Денежный прогноз"),
        KeyboardButton(text="💎 Баллы"),
    )
    builder.row(
        KeyboardButton(text="🩷 Поддержать автора"),
        KeyboardButton(text="ℹ️ О боте"),
    )
    builder.row(KeyboardButton(text="📜 Пользовательское соглашение"))
    return builder.as_markup(resize_keyboard=True)


def about_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да / Нет", callback_data="goto:yesno"),
        InlineKeyboardButton(text="🍀 Энергия года", callback_data="goto:energy"),
    )
    builder.row(
        InlineKeyboardButton(text="💰 Денежный прогноз", callback_data="goto:money"),
    )
    return builder.as_markup()


def back_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 В меню", callback_data="goto:menu")]
        ]
    )


def yes_no_confirm() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔮 Узнать ответ", callback_data="yesno:draw")],
            [InlineKeyboardButton(text="🏠 В меню", callback_data="goto:menu")],
        ]
    )


def energy_actions(has_birth: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_birth:
        builder.row(
            InlineKeyboardButton(
                text="✨ Рассчитать на этот год", callback_data="energy:calc:current"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="📅 Выбрать другой год", callback_data="energy:pick_year"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="✏️ Изменить дату рождения", callback_data="energy:set_birth"
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="📅 Указать дату рождения", callback_data="energy:set_birth"
            )
        )
    builder.row(InlineKeyboardButton(text="🏠 В меню", callback_data="goto:menu"))
    return builder.as_markup()


def money_actions(has_birth: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_birth:
        builder.row(
            InlineKeyboardButton(
                text="💰 Прогноз на этот год", callback_data="money:calc:current"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="📅 Выбрать другой год", callback_data="money:pick_year"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="✏️ Изменить дату рождения", callback_data="money:set_birth"
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="📅 Указать дату рождения", callback_data="money:set_birth"
            )
        )
    builder.row(InlineKeyboardButton(text="🏠 В меню", callback_data="goto:menu"))
    return builder.as_markup()


def year_picker(prefix: str, current_year: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    years = [current_year - 1, current_year, current_year + 1, current_year + 2]
    row: list[InlineKeyboardButton] = []
    for y in years:
        row.append(
            InlineKeyboardButton(text=str(y), callback_data=f"{prefix}:calc:{y}")
        )
    builder.row(*row)
    builder.row(
        InlineKeyboardButton(text="✏️ Ввести год", callback_data=f"{prefix}:year_input")
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data=f"goto:{prefix}"))
    return builder.as_markup()
