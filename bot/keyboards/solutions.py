from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def solutions_kb(is_staff: bool) -> ReplyKeyboardMarkup:
    rows = []
    if is_staff:
        rows.append([KeyboardButton(text="Все решения (staff)")])
    rows.append([KeyboardButton(text="Мои решения")])
    rows.append([KeyboardButton(text="Назад")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def staff_solutions_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Показать все решения")],
            [KeyboardButton(text="Последние 15 решений")],
            [KeyboardButton(text="Показать решения по городу")],
            [KeyboardButton(text="Показать решения по @username")],
            [KeyboardButton(text="Назад")],
        ],
        resize_keyboard=True,
    )
