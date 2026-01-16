from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.texts import WELCOME_TEXT

from bot.keyboards.common import main_menu_kb
from bot.states.game import GameStates

router = Router()

# обновим username в профиле, если пользователь уже есть


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, role, db, **_):
    await state.clear()

    img_url = "https://cyber.sports.ru/dota2/blogs/3232588.html"
    await message.answer_photo(
        photo=img_url,
        caption=WELCOME_TEXT,
        reply_markup=main_menu_kb(is_admin=role.is_admin),
    )

    user = await db.get_user(message.from_user.id)
    if user:
        await db.upsert_user(
            user_id=message.from_user.id,
            captain_name=user.get("captain_name") or "",
            username=message.from_user.username,
        )

    await message.answer("Введите ФИО капитана:")
    await state.set_state(GameStates.captain_name)

    
@router.message(F.text.in_({"Отмена", "В меню"}))
async def cancel_flow(message: Message, state: FSMContext, role, **_):
    await state.clear()
    await message.answer(
        "Ок, вернулись в меню.",
        reply_markup=main_menu_kb(is_admin=role.is_admin),
    )