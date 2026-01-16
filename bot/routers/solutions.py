from __future__ import annotations

from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext

from bot.utils.tg_render import render_report_md2
from bot.keyboards.common import main_menu_kb
from bot.keyboards.solutions import solutions_kb, staff_solutions_kb
from bot.decorators.access import mod_or_admin
from bot.states.staff import StaffSolutionsStates

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


def _build_card(
    text_1: str,
    text_2: str,
    report: str,
    prefix: str = "",
    meta: str = "",
) -> str:
    text_1 = (text_1 or "").strip()
    text_2 = (text_2 or "").strip()
    report = (report or "").strip()

    header_lines: list[str] = []
    if prefix:
        header_lines.append(prefix)
    if meta:
        header_lines.append(meta)

    header = ("\n".join(header_lines) + "\n\n") if header_lines else ""

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


async def _send_cards_text(message: Message, text: str) -> None:
    # РЕЖЕМ СЫРОЙ ТЕКСТ, а не готовый MarkdownV2
    for part in _split_telegram(text):
        msg_tg = render_report_md2(part)
        await message.answer(msg_tg, parse_mode=ParseMode.MARKDOWN_V2)


async def _send_staff_cards(
    message: Message,
    db,
    limit: int | None = 15,
    city: str | None = None,
    username: str | None = None,  # без "@"
) -> None:
    rows = await db.list_all_solutions()
    if not rows:
        await message.answer("Пока нет решений.")
        return

    # группируем по (owner_user_id, round_id)
    groups: dict[tuple[int, int], list[dict]] = {}
    for r in rows:
        key = (int(r["owner_user_id"]), int(r["round_id"]))
        groups.setdefault(key, []).append(r)

    keys = list(groups.keys())

    # фильтр по городу
    if city:
        city_norm = city.strip().lower()
        filtered: list[tuple[int, int]] = []
        for (uid, rid) in keys:
            u = await db.get_user(uid) or {}
            ucity = (u.get("city") or "").strip().lower()
            if ucity == city_norm:
                filtered.append((uid, rid))
        keys = filtered

    # фильтр по username
    if username:
        uname_norm = username.strip().lower()
        filtered: list[tuple[int, int]] = []
        for (uid, rid) in keys:
            u = await db.get_user(uid) or {}
            u_uname = (u.get("username") or "").strip().lower()
            if u_uname == uname_norm:
                filtered.append((uid, rid))
        keys = filtered

    # сортировка и лимит
    keys_sorted = sorted(keys, key=lambda x: (x[1], x[0]))
    if limit is not None:
        keys_sorted = keys_sorted[-limit:]

    if not keys_sorted:
        await message.answer("Ничего не найдено.")
        return

    for (uid, rid) in keys_sorted:
        items = groups[(uid, rid)]

        first = next((x for x in items if x.get("stage") == "first"), None)
        constrained = next((x for x in items if x.get("stage") == "constrained"), None)
        final_eval = next((x for x in items if x.get("stage") == "final_eval"), None)

        # профиль пользователя (для шапки)
        u = await db.get_user(uid) or {}
        uname = (u.get("username") or "").lstrip("@").strip()
        city_val = (u.get("city") or "").strip()
        fio = (u.get("captain_name") or "").strip()

        meta_parts: list[str] = []
        if uname:
            meta_parts.append(f"@{uname}")
        if city_val:
            meta_parts.append(f"город: {city_val}")
        if fio:
            meta_parts.append(f"ФИО: {fio}")

        meta = " | ".join(meta_parts)

        msg = _build_card(
            text_1=(first or {}).get("text"),
            text_2=(constrained or {}).get("text"),
            report=(final_eval or {}).get("gigachat_report"),
            prefix=f"user_id={uid}",
            meta=meta,
        )

        await _send_cards_text(message, msg)


@router.message(F.text == "Решения")
async def solutions_menu(message: Message, role, state: FSMContext, **_):
    await state.clear()
    is_staff = role.is_admin or role.is_moderator
    await message.answer("Выберите режим просмотра:", reply_markup=solutions_kb(is_staff=is_staff))

@router.message(F.text == "Назад")
async def back(message: Message, role, state: FSMContext, **_):
    # чтобы staff-режим ожидания ввода не мешал
    await state.clear()
    await message.answer("Главное меню.", reply_markup=main_menu_kb(is_admin=role.is_admin))


@router.message(F.text == "Мои решения")
async def my_solutions(message: Message, db, **_):
    rows = await db.list_my_solutions(message.from_user.id)
    if not rows:
        await message.answer("Пока нет решений.")
        return

    # группируем по round_id
    groups: dict[int, list[dict]] = {}
    for r in rows:
        rid = int(r["round_id"])
        groups.setdefault(rid, []).append(r)

    rids_sorted = sorted(groups.keys())
    limit = 15
    rids_sorted = rids_sorted[-limit:]

    for rid in rids_sorted:
        items = groups[rid]
        first = next((x for x in items if x.get("stage") == "first"), None)
        constrained = next((x for x in items if x.get("stage") == "constrained"), None)
        final_eval = next((x for x in items if x.get("stage") == "final_eval"), None)

        msg = _build_card(
            text_1=(first or {}).get("text"),
            text_2=(constrained or {}).get("text"),
            report=(final_eval or {}).get("gigachat_report"),
            prefix=f"round_id={rid}",
            meta="",  # можно добавить город/ФИО, если хочешь
        )

        msg_tg = render_report_md2(msg)
        for part in _split_telegram(msg_tg):
            await message.answer(part, parse_mode=ParseMode.MARKDOWN_V2)


# ---------- STAFF меню ----------

@router.message(F.text == "Все решения (staff)")
@mod_or_admin
async def all_solutions_staff_menu(message: Message, state: FSMContext, **_):
    await state.clear()
    await message.answer("Выбери какие решения показать:", reply_markup=staff_solutions_kb())


@router.message(F.text == "Все решения")
@mod_or_admin
async def staff_all(message: Message, db, **_):
    await _send_staff_cards(message, db, limit=None)


@router.message(F.text == "Показать последние 15 решений")
@mod_or_admin
async def staff_last15(message: Message, db, **_):
    await _send_staff_cards(message, db, limit=15)


@router.message(F.text == "Показать решения по городу")
@mod_or_admin
async def staff_city_ask(message: Message, state: FSMContext, **_):
    await message.answer("Введи город (например: Самара):")
    await state.set_state(StaffSolutionsStates.wait_city)


@router.message(StaffSolutionsStates.wait_city)
@mod_or_admin
async def staff_city_do(message: Message, state: FSMContext, db, **_):
    city = (message.text or "").strip()
    await state.clear()
    await _send_staff_cards(message, db, limit=15, city=city)


@router.message(F.text == "Показать решения по @username")
@mod_or_admin
async def staff_username_ask(message: Message, state: FSMContext, **_):
    await message.answer("Введи @username (например: @mrmax):")
    await state.set_state(StaffSolutionsStates.wait_username)


@router.message(StaffSolutionsStates.wait_username)
@mod_or_admin
async def staff_username_do(message: Message, state: FSMContext, db, **_):
    uname = (message.text or "").strip().lstrip("@")
    await state.clear()
    await _send_staff_cards(message, db, limit=15, username=uname)
