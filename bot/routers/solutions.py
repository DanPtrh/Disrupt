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
    # Telegram лимит ~4096, оставляем запас
    return [text[i:i + limit] for i in range(0, len(text), limit)]


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

    text_1 = ((first or {}).get("text") or "").strip()
    text_2 = ((constrained or {}).get("text") or "").strip()
    report = ((final_eval or {}).get("gigachat_report") or "").strip()

    msg = (
        "Этап 1 (без ограничения):\n"
        f"{text_1 if text_1 else '—'}\n\n"
        "Этап 2 (с ограничением):\n"
        f"{text_2 if text_2 else '—'}\n\n"
        "Общий отчёт гигачата:\n"
        f"{report if report else '—'}"
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

    # staff режим — последние 15 записей коротко (без гига-отчётов на 10 экранов)
    for r in rows[-15:]:
        preview = (r.get("text") or r.get("gigachat_report") or "").strip()
        if len(preview) > 900:
            preview = preview[:900] + "..."
        await message.answer(
            f"user_id={r['owner_user_id']} | stage={r['stage']}\n{preview}"
        )
