from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def user_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🟢 Начать день"),
                KeyboardButton(text="🔴 Закончить день"),
            ],
            [
                KeyboardButton(text="📊 Статистика"),
            ]
        ],
        resize_keyboard=True,
        persistent=True
    )