from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.decorators.access import admin_only
from bot.keyboards.admin import admin_panel_kb
from bot.keyboards.common import main_menu_kb
from aiogram.exceptions import TelegramForbiddenError
from bot.routers.start import show_main_menu

router = Router()

@router.message(F.text == "Админ панель")
@admin_only
async def admin_panel(message: Message, **_):
    await message.answer("Админ панель:", reply_markup=admin_panel_kb())

@router.message(F.text == "Назначить модератора")
@admin_only
async def ask_add_mod(message: Message, state: FSMContext, **_):
    await state.update_data(admin_action="add_mod")
    await message.answer("Пришлите user_id (числом) или @username человека, которому выдать модератора.")

"""
@router.message(F.text.regexp(r"^\d+$"))
async def numeric_message_router(message: Message, role, db, **_):
    # Примитивный режим: если админ открыл панель и прислал число — трактуем как действие.
    # В проде лучше сделать отдельные состояния FSM для админки.
    if not role.is_admin:
        return

    user_id = int(message.text)
    await db.add_moderator(user_id)
    await message.answer(f"Готово: user_id={user_id} теперь модератор.")
"""

@router.message(F.text == "Снять модератора")
@admin_only
async def ask_remove_mod(message: Message, state: FSMContext, **_):
    await state.update_data(admin_action="remove_mod")
    await message.answer("Пришлите user_id (числом) или @username человека, у которого снять модератора.")


@router.message(F.text == "Список модераторов")
@admin_only
async def list_mods(message: Message, db, **_):
    mods = await db.list_moderators()
    if not mods:
        await message.answer("Модераторов нет.")
        return

    lines = []
    for m in mods:
        uname = m.get("username")
        lines.append(f"{m['user_id']}" + (f" (@{uname})" if uname else ""))
    await message.answer("Модераторы:\n" + "\n".join(lines))


@router.message(F.text.in_({"Назад", "Главное меню"}))
async def back_from_admin(message: Message, role, state: FSMContext, db, **_):
    await state.clear()
    await show_main_menu(message, role, db)

@router.message()
async def admin_action_router(message: Message, state: FSMContext, role, db, **_):
    if not role.is_admin:
        return

    data = await state.get_data()
    action = data.get("admin_action")
    if action not in ("add_mod", "remove_mod"):
        return  # не в режиме админ-действия

    raw = (message.text or "").strip()

    # 1) если число — работаем как раньше
    if raw.isdigit():
        uid = int(raw)
    # 2) если @username — ищем в нашей базе модераторов ИЛИ в users.json
    elif raw.startswith("@"):
        uname = raw.lstrip("@").strip()
        # сначала попробуем найти среди уже назначенных модеров
        uid = await db.find_moderator_id_by_username(uname)

        # если не нашли — попробуем найти по users.json (если человек писал боту)
        if uid is None:
            users = await db._read(db.s.db_users_path)  # можно сделать отдельный метод, но быстро так
            uid = None
            for u in users:
                if (u.get("username") or "").lower() == uname.lower():
                    uid = int(u["user_id"])
                    break

        if uid is None:
            await message.answer(
                "Не удалось найти этого @username.\n"
                "Попросите пользователя написать боту /start или добавьте модератора по user_id."
            )
            return
    else:
        await message.answer("Пришлите user_id (числом) или @username.")
        return

    if action == "add_mod":
        username = raw.lstrip("@") if raw.startswith("@") else None
        await db.add_moderator(uid, username=username)
        await message.answer(f"Готово: user_id={uid} теперь модератор.")

        # уведомление пользователю
        try:
            await message.bot.send_message(
                chat_id=uid,
                text="Вас назначили модератором. Теперь доступен просмотр всех решений."
            )
        except TelegramForbiddenError:
            await message.answer(
                "Модератор назначен, но уведомление не доставлено: пользователь не запускал бота (/start) или запретил сообщения."
            )
    else:
        await db.remove_moderator(uid)
        await message.answer(f"Готово: user_id={uid} больше не модератор.")

        # опционально: уведомление о снятии
        try:
            await message.bot.send_message(
                chat_id=uid,
                text="У вас забрали права модератора."
            )
        except TelegramForbiddenError:
            pass
