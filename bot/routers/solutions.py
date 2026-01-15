from aiogram import Router, F
from aiogram.types import Message

from bot.keyboards.common import main_menu_kb
from bot.keyboards.solutions import solutions_kb
from bot.decorators.access import mod_or_admin

router = Router()


def _latest_round_id(rows: list[dict]) -> int | None:
    if not rows:
        return None
    return max(int(r["round_id"]) for r in rows)


def _find_stage(rows: list[dict], round_id: int, stage: str) -> dict | None:
    for r in rows:
        if int(r["round_id"]) == round_id and r.get("stage") == stage:
            return r
    return None


def _split_telegram(text: str, limit: int = 3900) -> list[str]:
    return [text[i:i + limit] for i in range(0, len(text), limit)]


def _build_card(text_1: str, text_2: str, report: str, prefix: str = "") -> str:
    text_1 = (text_1 or "").strip()
    text_2 = (text_2 or "").strip()
    report = (report or "").strip()

    header = (prefix + "\n") if prefix else ""

    return (
        header
        + "Этап 1 (без ограничения):\n"
        + (text_1 if text_1 else "—")
        + "\n\n"
        + "Этап 2 (с ограничением):\n"
        + (text_2 if text_2 else "—")
        + "\n\n"
        + "Общий отчёт гигачата:\n"
        + (report if report else "—")
    )


@router.message(F.text == "Решения")
async def solutions_menu(message: Message, role, **_):
    is_staff = role.is_admin or role.is_moderator
    await message.answer("Выберите режим просмотра:", reply_markup=solutions_kb(is_staff=is_staff))


@router.message(F.text == "Назад")
async def back(message: Message, role, **_):
    await message.answer("Главное меню.", reply_markup=main_menu_kb(is_admin=role.is_admin))


@router.message(F.text == "Мои решения")
async def my_solutions(message: Message, db, **_):
    rows = await db.list_my_solutions(message.from_user.id)
    if not rows:
        await message.answer("Пока нет решений.")
        return

    rid = _latest_round_id(rows)
    if rid is None:
        await message.answer("Пока нет решений.")
        return

    first = _find_stage(rows, rid, "first")
    constrained = _find_stage(rows, rid, "constrained")
    final_eval = _find_stage(rows, rid, "final_eval")

    msg = _build_card(
        text_1=(first or {}).get("text"),
        text_2=(constrained or {}).get("text"),
        report=(final_eval or {}).get("gigachat_report"),
        prefix="",  # без user_id
    )

    for part in _split_telegram(msg):
        await message.answer(part)


@router.message(F.text == "Все решения (staff)")
@mod_or_admin
async def all_solutions_staff(message: Message, db, **_):
    rows = await db.list_all_solutions()
    if not rows:
        await message.answer("Пока нет решений.")
        return

    # 1) группируем по (owner_user_id, round_id)
    groups: dict[tuple[int, int], list[dict]] = {}
    for r in rows:
        key = (int(r["owner_user_id"]), int(r["round_id"]))
        groups.setdefault(key, []).append(r)

    # 2) для стабильности сортируем группы: сначала по round_id, потом user_id
    keys_sorted = sorted(groups.keys(), key=lambda x: (x[1], x[0]))

    # 3) чтобы не спамить в чат — выводим последние 10 "карточек"
    keys_sorted = keys_sorted[-10:]

    for (uid, rid) in keys_sorted:
        items = groups[(uid, rid)]

        first = next((x for x in items if x.get("stage") == "first"), None)
        constrained = next((x for x in items if x.get("stage") == "constrained"), None)
        final_eval = next((x for x in items if x.get("stage") == "final_eval"), None)

        msg = _build_card(
            text_1=(first or {}).get("text"),
            text_2=(constrained or {}).get("text"),
            report=(final_eval or {}).get("gigachat_report"),
            prefix=f"user_id={uid}",
        )

        for part in _split_telegram(msg):
            await message.answer(part)
