from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.texts import RULES_TEXT
from bot.states.game import GameStates
from bot.services.randomizer import pick_base, pick_ogran
from bot.services.gigachat_service import GigaChatService


router = Router()


@router.message(GameStates.captain_name)
async def captain_name(message: Message, state: FSMContext, db, **_):
    captain = (message.text or "").strip()
    if len(captain) < 2:
        await message.answer("Имя слишком короткое. Введите имя капитана ещё раз:")
        return

    await db.upsert_user(message.from_user.id, captain)
    await message.answer("Введите название команды:")
    await state.set_state(GameStates.team_name)


@router.message(GameStates.team_name)
async def team_name(message: Message, state: FSMContext, db, **_):
    team = (message.text or "").strip()
    if len(team) < 2:
        await message.answer("Название слишком короткое. Введите название команды ещё раз:")
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
        "Пришлите решение одним сообщением."
    )
    await state.set_state(GameStates.first_solution)


@router.message(GameStates.first_solution)
async def first_solution(message: Message, state: FSMContext, db, **_):
    solution = (message.text or "").strip()
    if len(solution) < 300:
        await message.answer("Слишком коротко. Пришлите решение подробнее (минимум 300 символов).")
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
        "при разработке своей механики."
    )

    ogran = pick_ogran()
    await db.set_round_ogran(round_id, ogran)
    await message.answer(
        f"Ваше ограничение:\n{ogran}\n\n"
        "Пришлите обновлённое решение с учетом ограничения одним сообщением."
    )
    await state.set_state(GameStates.constrained_solution)


@router.message(GameStates.constrained_solution)
async def constrained_solution(message: Message, state: FSMContext, settings, db, **_):
    solution = (message.text or "").strip()
    if len(solution) < 300:
        await message.answer("Слишком коротко. Пришлите обновлённое решение подробнее (минимум 300 символов).")
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
    await message.answer("Готово! Общий отчёт сохранён. Открой «Решения» → «Мои решения».")

    await state.clear()
