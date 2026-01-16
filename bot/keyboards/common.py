from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_kb(is_admin: bool) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="/start")],
        [KeyboardButton(text="Решения")],
        [KeyboardButton(text="В меню")],
    ]
    if is_admin:
        rows.append([KeyboardButton(text="Админ панель")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
