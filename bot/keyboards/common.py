from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

def main_menu_kb(is_admin: bool) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="Начать игру")],
        [KeyboardButton(text="Решения")],
    ]
    if is_admin:
        rows.append([KeyboardButton(text="Админ панель")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def game_kb() -> ReplyKeyboardMarkup:
    """Клавиатура для использования во время игры"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Главное меню")],
        ],
        resize_keyboard=True,
    )
