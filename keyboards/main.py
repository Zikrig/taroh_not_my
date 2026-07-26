from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🃏 Карта дня", callback_data="menu:daycard"))
    builder.row(
        InlineKeyboardButton(text="✅ Да / Нет", callback_data="goto:yesno"),
        InlineKeyboardButton(text="🍀 Энергия года", callback_data="goto:energy"),
    )
    builder.row(
        InlineKeyboardButton(text="💰 Денежный прогноз", callback_data="goto:money"),
        InlineKeyboardButton(text="💎 Баллы", callback_data="bal:main"),
    )
    builder.row(InlineKeyboardButton(text="📂 Другое", callback_data="goto:other"))
    return builder.as_markup()


def other_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="ℹ️ О боте", callback_data="other:about"))
    builder.row(
        InlineKeyboardButton(text="🩷 Поддержать автора", callback_data="support:main")
    )
    builder.row(
        InlineKeyboardButton(
            text="📜 Пользовательское соглашение", callback_data="other:agreement"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="✏️ Изменить дату рождения", callback_data="other:set_birth"
        )
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="goto:menu"))
    return builder.as_markup()


def back_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ В меню", callback_data="goto:menu")]
        ]
    )


def back_other() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="goto:other")]
        ]
    )


def yes_no_confirm() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔮 Узнать ответ", callback_data="yesno:draw")
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="goto:menu"))
    return builder.as_markup()


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
    else:
        builder.row(
            InlineKeyboardButton(
                text="📅 Указать дату рождения", callback_data="other:set_birth"
            )
        )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="goto:menu"))
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
    else:
        builder.row(
            InlineKeyboardButton(
                text="📅 Указать дату рождения", callback_data="other:set_birth"
            )
        )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="goto:menu"))
    return builder.as_markup()


def year_picker(prefix: str, current_year: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    years = [current_year - 1, current_year, current_year + 1, current_year + 2]
    row = [
        InlineKeyboardButton(text=str(y), callback_data=f"{prefix}:calc:{y}")
        for y in years
    ]
    builder.row(*row)
    builder.row(
        InlineKeyboardButton(text="✏️ Ввести год", callback_data=f"{prefix}:year_input")
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data=f"goto:{prefix}"))
    return builder.as_markup()


def insufficient_funds_keyboard() -> InlineKeyboardMarkup:
    """Баллы выше, «Назад» ниже."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💎 Баллы", callback_data="bal:main"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="goto:menu"))
    return builder.as_markup()


def cancel_input_keyboard(back_to: str = "goto:other") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Отмена", callback_data=back_to)]
        ]
    )
