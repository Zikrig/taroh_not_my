from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from keyboards.buy import support_keyboard
from keyboards.main import about_menu

router = Router()

ABOUT_TEXT = (
    "🪳 Привет! Я Аркаша ТАРОкаша!\n\n"
    "Добро пожаловать в мой сказочный лес, где каждая карта хранит маленькое волшебство. 🌿✨\n"
    "Каждый день я и мои добрые друзья — пчёлки, бабочки, светлячки и другие лесные букашки — "
    "будем доставать для тебя Карту дня, чтобы подарить вдохновение, добрый совет или маленькую подсказку. 🍀\n\n"
    "🌼 Карта обновляется ежедневно.\n"
    "🎁 Это совершенно бесплатно.\n\n"
    "Но это ещё не всё! 🍄 В моём лесу ты также можешь:\n"
    "✨ получить ответ «Да / Нет» на волнующий вопрос;\n"
    "🍀 узнать Энергию года;\n"
    "💰 заглянуть в Денежный прогноз.\n\n"
    "Подробности о каждом разделе — по кнопкам ниже. 🌼\n\n"
    "Спасибо, что заглянул в наш лес! Располагайся поудобнее… Перемешиваем колоду? 🍃🔮\n"
    "Карты уже шуршат! 🪳✨"
)

AGREEMENT = (
    "<b>Пользовательское соглашение</b>\n\n"
    "1. <b>Развлекательный характер</b>\n"
    "Вся информация, предоставляемая данным ботом, носит исключительно развлекательный характер.\n\n"
    "2. <b>Отказ от ответственности</b>\n"
    "Автор бота не несёт никакой ответственности за точность, полноту или достоверность информации, "
    "предоставляемой ботом. Использование бота осуществляется на ваш страх и риск.\n\n"
    "3. <b>Условия покупок</b>\n"
    "Все покупки являются окончательными и не подлежат возврату, обмену или компенсации.\n\n"
    "4. <b>Принятие условий</b>\n"
    "Продолжая пользоваться ботом, вы соглашаетесь с условиями данного соглашения.\n"
    "Если вы не согласны с данными условиями, пожалуйста, прекратите использование бота."
)

SUPPORT = (
    "🩷 Аркаша ТАРОкаша создан с любовью и добрыми намерениями 🔮\n"
    "Поддерживая автора, ты помогаешь этому проекту расти, нести больше света и улыбок каждый день ✨\n\n"
    "Выбери сумму поддержки:"
)


@router.message(F.text == "ℹ️ О боте")
async def about_bot(message: Message) -> None:
    await message.answer(ABOUT_TEXT, reply_markup=about_menu())


@router.message(F.text == "📜 Пользовательское соглашение")
async def agreement(message: Message) -> None:
    await message.answer(AGREEMENT, parse_mode="HTML")


@router.message(F.text == "🩷 Поддержать автора")
async def support_author(message: Message) -> None:
    await message.answer(SUPPORT, reply_markup=support_keyboard())


@router.callback_query(F.data == "support:main")
async def support_main(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(SUPPORT, reply_markup=support_keyboard())
