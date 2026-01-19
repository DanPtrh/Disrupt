from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def admin_panel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Назначить модератора")],
            [KeyboardButton(text="Снять модератора")],
            [KeyboardButton(text="Список модераторов")],
            [KeyboardButton(text="Главное меню")],
        ],
        resize_keyboard=True,
    )
