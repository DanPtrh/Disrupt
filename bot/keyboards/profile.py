from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def profile_menu_kb() -> ReplyKeyboardMarkup:
    """Меню управления профилем"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Изменить ФИО")],
            [KeyboardButton(text="Изменить город")],
            [KeyboardButton(text="Изменить название команды")],
            [KeyboardButton(text="Главное меню")],
        ],
        resize_keyboard=True,
    )
