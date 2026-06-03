"""
Админ-панель: добавление рабочих дней, просмотр записей.
"""

from datetime import date

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from config import settings
from database import db
from keyboards.calendar import build_calendar_keyboard, get_schedule_date_range
from keyboards.inline import admin_panel_keyboard, back_to_menu_keyboard
from states.fsm import AdminStates
from utils.texts import format_cancelled_bookings_list, format_date_full_ru

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id == settings.admin_id and settings.admin_id != 0


@router.callback_query(F.data == "admin:panel")
async def admin_panel(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён.", show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text(
        "<b>⚙️ Админ-панель</b>\n\n"
        "Управление расписанием встреч:",
        reply_markup=admin_panel_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:add_day")
async def admin_add_day_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён.", show_alert=True)
        return

    today = date.today()
    min_d, max_d = get_schedule_date_range(today)
    # В админ-календаре доступны все дни в диапазоне (для добавления)
    all_days = set()
    current = min_d
    from datetime import timedelta

    while current <= max_d:
        all_days.add(current)
        current += timedelta(days=1)

    keyboard = await build_calendar_keyboard(
        year=today.year,
        month=today.month,
        available_dates=all_days,
        min_date=min_d,
        max_date=max_d,
        callback_prefix="admin:cal",
    )
    await state.set_state(AdminStates.choosing_work_day)
    await callback.message.edit_text(
        "<b>➕ Добавить рабочий день</b>\n\n"
        "Выбери дату в календаре:",
        reply_markup=keyboard,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:cal:nav:"))
async def admin_calendar_nav(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        return
    part = callback.data.split(":")[-1]
    year, month = map(int, part.split("-"))
    today = date.today()
    min_d, max_d = get_schedule_date_range(today)

    from datetime import timedelta

    all_days = set()
    current = min_d
    while current <= max_d:
        all_days.add(current)
        current += timedelta(days=1)

    keyboard = await build_calendar_keyboard(
        year=year,
        month=month,
        available_dates=all_days,
        min_date=min_d,
        max_date=max_d,
        callback_prefix="admin:cal",
    )
    await callback.message.edit_text(
        "<b>➕ Добавить рабочий день</b>\n\n"
        "Выбери дату в календаре:",
        reply_markup=keyboard,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:cal:day:"))
async def admin_select_day(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        return

    day_str = callback.data.split(":")[-1]
    selected = date.fromisoformat(day_str)
    added = await db.add_working_day(selected)

    await state.clear()
    if added:
        text = (
            f"<b>✅ Рабочий день добавлен</b>\n\n"
            f"📅 {format_date_full_ru(selected)}"
        )
    else:
        text = (
            f"<b>ℹ️ День уже в расписании</b>\n\n"
            f"📅 {format_date_full_ru(selected)}"
        )

    await callback.message.edit_text(text, reply_markup=admin_panel_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:bookings")
async def admin_bookings(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён.", show_alert=True)
        return

    bookings = await db.get_all_active_bookings()
    if not bookings:
        text = "<b>📋 Активные записи</b>\n\n<i>Записей пока нет.</i>"
    else:
        lines = ["<b>📋 Активные записи</b>\n"]
        for b in bookings:
            d = date.fromisoformat(b["date"])
            name = b.get("full_name") or "—"
            uname = f"@{b['username']}" if b.get("username") else ""
            lines.append(
                f"\n🆔 <code>{b['id']}</code>\n"
                f"👤 {name} {uname}\n"
                f"📅 {format_date_full_ru(d)} в <b>{b['time']}</b>"
            )
        text = "\n".join(lines)

    await callback.message.edit_text(text, reply_markup=admin_panel_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:cancelled")
async def admin_cancelled_bookings(callback: CallbackQuery) -> None:
    """Список отменённых встреч."""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён.", show_alert=True)
        return

    bookings = await db.get_cancelled_bookings()
    text = format_cancelled_bookings_list(bookings)
    await callback.message.edit_text(text, reply_markup=admin_panel_keyboard())
    await callback.answer()
