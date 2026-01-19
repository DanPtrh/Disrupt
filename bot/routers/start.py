from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.texts import WELCOME_TEXT

from bot.keyboards.common import main_menu_kb
from bot.states.game import GameStates

router = Router()

# обновим username в профиле, если пользователь уже есть


async def show_main_menu(message: Message, role, db):
    """Показывает главное меню с приветственным сообщением и картинкой"""
    # Обновляем username в профиле, если пользователь уже есть
    user = await db.get_user(message.from_user.id)
    if user:
        await db.upsert_user(
            user_id=message.from_user.id,
            captain_name=user.get("captain_name") or "",
            username=message.from_user.username,
        )

    img_url = "https://cyber.sports.ru/dota2/blogs/3232588.html"
    await message.answer_photo(
        photo=img_url,
        caption=WELCOME_TEXT,
        reply_markup=main_menu_kb(is_admin=role.is_admin),
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, role, db, **_):
    await state.clear()
    await show_main_menu(message, role, db)


@router.message(F.text.in_({"Отмена", "В меню", "Главное меню"}))
async def cancel_flow(message: Message, state: FSMContext, role, db, **_):
    await state.clear()
    await show_main_menu(message, role, db)