from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.keyboards.profile import profile_menu_kb
from bot.keyboards.common import game_kb
from bot.states.profile import ProfileStates
from bot.routers.start import show_main_menu

router = Router()


@router.message(F.text == "Профиль")
async def show_profile(message: Message, state: FSMContext, db, **_):
    """Показать текущий профиль пользователя"""
    await state.clear()

    user = await db.get_user(message.from_user.id)
    team = await db.get_team(message.from_user.id)

    captain_name = user.get("captain_name", "Не указано") if user else "Не указано"
    city = user.get("city", "Не указан") if user else "Не указан"
    team_name = team.get("team_name", "Не указана") if team else "Не указана"
    username = f"@{message.from_user.username}" if message.from_user.username else "Не указан"

    profile_text = (
        f"Ваш профиль:\n\n"
        f"ФИО капитана: {captain_name}\n"
        f"Город: {city}\n"
        f"Название команды: {team_name}\n"
        f"Telegram: {username}\n\n"
        f"Выберите, что хотите изменить:"
    )

    await message.answer(profile_text, reply_markup=profile_menu_kb())


@router.message(F.text == "Изменить ФИО")
async def edit_captain_name_start(message: Message, state: FSMContext, **_):
    """Начать редактирование ФИО"""
    await message.answer("Введите новое ФИО капитана:", reply_markup=game_kb())
    await state.set_state(ProfileStates.edit_captain_name)


@router.message(ProfileStates.edit_captain_name)
async def edit_captain_name_finish(message: Message, state: FSMContext, db, **_):
    """Сохранить новое ФИО"""
    captain = (message.text or "").strip()

    # Игнорируем системные кнопки
    system_buttons = {"Главное меню", "В меню", "Отмена", "Начать игру", "Решения", "Админ панель", "Профиль"}
    if captain in system_buttons:
        return

    if len(captain) < 2:
        await message.answer("Имя слишком короткое. Введите ФИО капитана ещё раз:", reply_markup=game_kb())
        return

    # Обновляем ФИО
    await db.upsert_user(
        user_id=message.from_user.id,
        captain_name=captain,
        username=message.from_user.username,
    )

    await state.clear()
    await message.answer(
        f"ФИО капитана успешно обновлено на: {captain}",
        reply_markup=profile_menu_kb()
    )


@router.message(F.text == "Изменить город")
async def edit_city_start(message: Message, state: FSMContext, **_):
    """Начать редактирование города"""
    await message.answer(
        "Введите новый город (С большой буквы без пробелов. Пример: Санктпетербург, Нижнийновгород):",
        reply_markup=game_kb()
    )
    await state.set_state(ProfileStates.edit_city)


@router.message(ProfileStates.edit_city)
async def edit_city_finish(message: Message, state: FSMContext, db, **_):
    """Сохранить новый город"""
    city = (message.text or "").strip()

    # Игнорируем системные кнопки
    system_buttons = {"Главное меню", "В меню", "Отмена", "Начать игру", "Решения", "Админ панель", "Профиль"}
    if city in system_buttons:
        return

    if len(city) < 2:
        await message.answer("Город слишком короткий. Введите город ещё раз:", reply_markup=game_kb())
        return

    # Обновляем город
    await db.set_user_city(message.from_user.id, city)

    await state.clear()
    await message.answer(
        f"Город успешно обновлен на: {city}",
        reply_markup=profile_menu_kb()
    )


@router.message(F.text == "Изменить название команды")
async def edit_team_start(message: Message, state: FSMContext, **_):
    """Начать редактирование названия команды"""
    await message.answer("Введите новое название команды:", reply_markup=game_kb())
    await state.set_state(ProfileStates.edit_team_name)


@router.message(ProfileStates.edit_team_name)
async def edit_team_finish(message: Message, state: FSMContext, db, **_):
    """Сохранить новое название команды"""
    team = (message.text or "").strip()

    # Игнорируем системные кнопки
    system_buttons = {"Главное меню", "В меню", "Отмена", "Начать игру", "Решения", "Админ панель", "Профиль"}
    if team in system_buttons:
        return

    if len(team) < 2:
        await message.answer("Название слишком короткое. Введите название команды ещё раз:", reply_markup=game_kb())
        return

    # Обновляем команду
    await db.upsert_team(message.from_user.id, team)

    await state.clear()
    await message.answer(
        f"Название команды успешно обновлено на: {team}",
        reply_markup=profile_menu_kb()
    )


@router.message(F.text.in_({"Назад", "Главное меню"}))
async def back_to_main(message: Message, state: FSMContext, role, db, **_):
    """Вернуться в главное меню"""
    await state.clear()
    await show_main_menu(message, role, db)
