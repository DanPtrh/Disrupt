from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from bot.texts import RULES_TEXT
from bot.states.game import GameStates
from bot.services.randomizer import pick_base, pick_ogran
from bot.services.gigachat_service import GigaChatService
from bot.keyboards.common import main_menu_kb, game_kb


router = Router()


@router.message(F.text == "Начать игру")
async def start_game(message: Message, state: FSMContext, db, role, **_):
    """Обработчик кнопки 'Начать игру' - проверяет регистрацию и либо запрашивает данные, либо начинает игру"""
    await state.clear()

    user = await db.get_user(message.from_user.id)
    team = await db.get_team(message.from_user.id)

    # Проверяем, есть ли все необходимые данные для игры
    has_captain = user and user.get("captain_name") and len(user.get("captain_name", "").strip()) >= 2
    has_city = user and user.get("city") and len(user.get("city", "").strip()) >= 2
    has_team = team and team.get("team_name") and len(team.get("team_name", "").strip()) >= 2

    if has_captain and has_city and has_team:
        # Пользователь уже зарегистрирован - начинаем новую игру
        pack = pick_base()
        round_id = await db.create_round(
            user_id=message.from_user.id,
            audit=pack.audit,
            product=pack.product,
            activity=pack.activity,
        )
        await state.update_data(round_id=round_id)

        await message.answer(
            f"Правила игры:\n\n{RULES_TEXT}\n\n"
            f"ЦА: {pack.audit}\n"
            f"Продукт: {pack.product}\n"
            f"Активность: {pack.activity}\n\n"
            "Начинаем генерить идеи! Придумайте стратегию продвижения продукта для целевой аудитории путём определённой активности.\n"
            "У вас на это 20 минут!\n\n"
            "Пришлите решение одним сообщением.",
            reply_markup=game_kb()
        )
        await state.set_state(GameStates.first_solution)
    else:
        # Пользователь не зарегистрирован - запрашиваем данные
        await message.answer("Введите ФИО капитана:", reply_markup=game_kb())
        await state.set_state(GameStates.captain_name)


@router.message(GameStates.captain_name)
async def captain_name(message: Message, state: FSMContext, db, **_):
    captain = (message.text or "").strip()

    # Игнорируем системные кнопки
    system_buttons = {"Главное меню", "В меню", "Отмена", "Начать игру", "Решения", "Админ панель", "Профиль"}
    if captain in system_buttons:
        return

    if len(captain) < 2:
        await message.answer("Имя слишком короткое. Введите имя капитана ещё раз:", reply_markup=game_kb())
        return

    # сохраняем ФИО + username (чтобы потом можно было искать по @)
    await db.upsert_user(
        user_id=message.from_user.id,
        captain_name=captain,
        username=message.from_user.username,
    )

    await message.answer(
        "Введите город (С большой буквы без пробелов. Пример: Санктпетербург, Нижнийновгород):",
        reply_markup=game_kb()
    )
    await state.set_state(GameStates.city)

@router.message(GameStates.city)
async def city(message: Message, state: FSMContext, db, **_):
    city = (message.text or "").strip()

    # Игнорируем системные кнопки
    system_buttons = {"Главное меню", "В меню", "Отмена", "Начать игру", "Решения", "Админ панель", "Профиль"}
    if city in system_buttons:
        return

    if len(city) < 2:
        await message.answer("Город слишком короткий. Введите город ещё раз:", reply_markup=game_kb())
        return

    await db.set_user_city(message.from_user.id, city)

    await message.answer("Введите название команды:", reply_markup=game_kb())
    await state.set_state(GameStates.team_name)


@router.message(GameStates.team_name)
async def team_name(message: Message, state: FSMContext, db, **_):
    team = (message.text or "").strip()

    # Игнорируем системные кнопки
    system_buttons = {"Главное меню", "В меню", "Отмена", "Начать игру", "Решения", "Админ панель", "Профиль"}
    if team in system_buttons:
        return

    if len(team) < 2:
        await message.answer("Название слишком короткое. Введите название команды ещё раз:", reply_markup=game_kb())
        return

    user_id = message.from_user.id
    await db.upsert_team(user_id, team)

    pack = pick_base()
    round_id = await db.create_round(
        user_id=user_id,
        audit=pack.audit,
        product=pack.product,
        activity=pack.activity,
    )
    await state.update_data(round_id=round_id)

    await message.answer(
        f"Правила игры:\n\n{RULES_TEXT}\n\n"
        f"ЦА: {pack.audit}\n"
        f"Продукт: {pack.product}\n"
        f"Активность: {pack.activity}\n\n"
        "Начинаем генерить идеи! Придумайте стратегию продвижения продукта для целевой аудитории путём определённой активности.\n"
        "У вас на это 20 минут!\n\n"
        "Пришлите решение одним сообщением.",
        reply_markup=game_kb()
    )
    await state.set_state(GameStates.first_solution)


@router.message(GameStates.first_solution)
async def first_solution(message: Message, state: FSMContext, db, **_):
    solution = (message.text or "").strip()
    if len(solution) < 300:
        await message.answer(
            "Слишком коротко. Пришлите решение подробнее (минимум 300 символов).",
            reply_markup=game_kb()
        )
        return

    data = await state.get_data()
    round_id = data["round_id"]

    # Сохраняем этап 1 (без оценки)
    await db.save_solution(
        owner_user_id=message.from_user.id,
        round_id=round_id,
        stage="first",
        text=solution,
        gigachat_report="",
        score=0,
    )

    await message.answer(
        "Упссс….\n"
        "Как это бывает в реальной жизни, всегда появляются дополнительные условия, с которыми нам нужно тоже работать! "
        "От этого наш процесс станет только интереснее! Каждая команда выберет себе дополнительное условие, которое нужно учесть "
        "при разработке своей механики.",
        reply_markup=game_kb()
    )

    ogran = pick_ogran()
    await db.set_round_ogran(round_id, ogran)
    await message.answer(
        f"Ваше ограничение:\n{ogran}\n\n"
        "Пришлите обновлённое решение с учетом ограничения одним сообщением.",
        reply_markup=game_kb()
    )
    await state.set_state(GameStates.constrained_solution)


@router.message(GameStates.constrained_solution)
async def constrained_solution(message: Message, state: FSMContext, settings, db, role, **_):
    solution = (message.text or "").strip()
    if len(solution) < 300:
        await message.answer(
            "Слишком коротко. Пришлите обновлённое решение подробнее (минимум 300 символов).",
            reply_markup=game_kb()
        )
        return

    data = await state.get_data()
    round_id = data["round_id"]
    rnd = await db.get_round(round_id)
    ogran = rnd.get("ogran") or "—"

    # Сохраняем этап 2 (без оценки)
    await db.save_solution(
        owner_user_id=message.from_user.id,
        round_id=round_id,
        stage="constrained",
        text=solution,
        gigachat_report="",
        score=0,
    )

    # Достаём оба решения для общего отчёта
    sols = await db.get_round_solutions(round_id=round_id, owner_user_id=message.from_user.id)
    first_text = (sols["first"]["text"] if sols["first"] else "")
    constrained_text = solution

    team = await db.get_team(message.from_user.id)
    team_name = (team["team_name"] if team else "Без названия")

    # ОДИН вызов гигачата (общий отчёт по двум решениям)
    giga = GigaChatService(
        credentials=settings.gigachat_credentials,
        scope=settings.gigachat_scope,
        verify_ssl=settings.gigachat_verify_ssl,
    )

    score, report = await giga.evaluate_final(
        team_name=team_name,
        audit=rnd["audit"],
        product=rnd["product"],
        activity=rnd["activity"],
        ogran=ogran,
        solution_first=first_text,
        solution_constrained=constrained_text,
    )

    # Сохраняем общий отчёт отдельно
    await db.save_solution(
        owner_user_id=message.from_user.id,
        round_id=round_id,
        stage="final_eval",
        text="",
        gigachat_report=report,
        score=score,
    )

    # Можно не показывать тут, если хочешь видеть только через "Мои решения"
    await message.answer(
        "Готово! Общий отчёт сохранён. Открой «Решения» → «Мои решения».",
        reply_markup=main_menu_kb(is_admin=role.is_admin)
    )

    await state.clear()
