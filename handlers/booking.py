"""
Запись на свидание: календарь, время, подтверждение, отмена.
"""

from datetime import date

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from config import settings
from database import db
from keyboards.calendar import build_calendar_keyboard, get_schedule_date_range
from keyboards.inline import (
    back_to_menu_keyboard,
    confirm_keyboard,
    main_menu_keyboard,
    time_slots_keyboard,
)
from states.fsm import BookingStates
from utils.channel import update_channel_schedule
from utils.scheduler import ReminderScheduler
from utils.notify import notify_admin
from utils.texts import (
    format_admin_cancel_notify,
    format_admin_notify,
    format_booking_confirm,
    format_booking_success,
    format_date_full_ru,
    format_user_booking,
)

router = Router()


async def _get_available_dates_set() -> set[date]:
    """Рабочие дни с хотя бы одним свободным слотом."""
    today = date.today()
    min_d, max_d = get_schedule_date_range(today)
    working = await db.get_working_days_between(min_d, max_d)
    result: set[date] = set()
    for d in working:
        if d < today:
            continue
        slots = await db.get_available_slots(d)
        if slots:
            result.add(d)
    return result


async def _show_calendar(callback: CallbackQuery, state: FSMContext, year: int, month: int) -> None:
    """Показать календарь выбора даты."""
    today = date.today()
    min_d, max_d = get_schedule_date_range(today)
    available = await _get_available_dates_set()

    if not available:
        await callback.message.edit_text(
            "<b>😔 Пока нет свободных дат</b>\n\n"
            "Администратор ещё не добавил рабочие дни или все слоты заняты.\n"
            "Загляни позже!",
            reply_markup=back_to_menu_keyboard(),
        )
        await state.clear()
        await callback.answer()
        return

    keyboard = await build_calendar_keyboard(
        year=year,
        month=month,
        available_dates=available,
        min_date=min_d,
        max_date=max_d,
        callback_prefix="book:cal",
    )
    await state.set_state(BookingStates.choosing_date)
    await callback.message.edit_text(
        "<b>📅 Выбери дату встречи</b>\n\n"
        "<i>Доступны только свободные дни в ближайший месяц.</i>",
        reply_markup=keyboard,
    )
    await callback.answer()


@router.callback_query(F.data == "book:start")
async def book_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Начать запись."""
    existing = await db.get_active_booking_by_user(callback.from_user.id)
    if existing:
        d = date.fromisoformat(existing["date"])
        await callback.message.edit_text(
            "<b>⚠️ У тебя уже есть запись</b>\n\n"
            + format_user_booking(d, existing["time"]),
            reply_markup=back_to_menu_keyboard(),
        )
        await callback.answer()
        return

    today = date.today()
    await _show_calendar(callback, state, today.year, today.month)


@router.callback_query(F.data.startswith("book:cal:nav:"))
async def book_calendar_nav(callback: CallbackQuery, state: FSMContext) -> None:
    """Перелистывание месяца."""
    part = callback.data.split(":")[-1]
    year, month = map(int, part.split("-"))
    await _show_calendar(callback, state, year, month)


@router.callback_query(F.data.startswith("book:cal:day:"))
async def book_select_date(callback: CallbackQuery, state: FSMContext) -> None:
    """Выбор даты → показ слотов времени."""
    day_str = callback.data.split(":")[-1]
    selected = date.fromisoformat(day_str)

    slots = await db.get_available_slots(selected)
    if not slots:
        await callback.answer("Эта дата уже занята. Выбери другую.", show_alert=True)
        return

    await state.update_data(selected_date=day_str)
    await state.set_state(BookingStates.choosing_time)
    await callback.message.edit_text(
        f"<b>🕐 Выбери время</b>\n\n"
        f"📅 Дата: <b>{format_date_full_ru(selected)}</b>",
        reply_markup=time_slots_keyboard(slots),
    )
    await callback.answer()


@router.callback_query(F.data == "book:back_to_calendar")
async def book_back_calendar(callback: CallbackQuery, state: FSMContext) -> None:
    today = date.today()
    await _show_calendar(callback, state, today.year, today.month)


@router.callback_query(F.data.startswith("book:time:"))
async def book_select_time(callback: CallbackQuery, state: FSMContext) -> None:
    """Выбор времени → подтверждение."""
    time_slot = callback.data.split(":", 2)[-1]
    data = await state.get_data()
    day_str = data.get("selected_date")
    if not day_str:
        await callback.answer("Сначала выбери дату.", show_alert=True)
        return

    selected = date.fromisoformat(day_str)
    if await db.is_slot_taken(selected, time_slot):
        await callback.answer("Это время уже занято.", show_alert=True)
        return

    await state.update_data(selected_time=time_slot)
    await state.set_state(BookingStates.confirming)
    await callback.message.edit_text(
        format_booking_confirm(selected, time_slot),
        reply_markup=confirm_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "book:confirm:no")
async def book_confirm_no(callback: CallbackQuery, state: FSMContext) -> None:
    """Отказ от встречи."""
    await state.clear()
    has_booking = await db.get_active_booking_by_user(callback.from_user.id) is not None
    is_admin = callback.from_user.id == settings.admin_id
    await callback.message.edit_text(
        "<b>Хорошо 💫</b>\n\n"
        "Если передумаешь — всегда можешь записаться снова.",
        reply_markup=main_menu_keyboard(is_admin, has_booking),
    )
    await callback.answer()


@router.callback_query(F.data == "book:confirm:yes")
async def book_confirm_yes(
    callback: CallbackQuery,
    state: FSMContext,
    reminder_scheduler: ReminderScheduler,
) -> None:
    """Подтверждение — сохранение, уведомления, напоминание."""
    data = await state.get_data()
    day_str = data.get("selected_date")
    time_slot = data.get("selected_time")
    if not day_str or not time_slot:
        await callback.answer("Данные устарели. Начни заново.", show_alert=True)
        return

    selected = date.fromisoformat(day_str)
    user = callback.from_user

    if await db.get_active_booking_by_user(user.id):
        await callback.answer("У тебя уже есть активная запись.", show_alert=True)
        return
    if await db.is_slot_taken(selected, time_slot):
        await callback.answer("Слот уже занят. Выбери другое время.", show_alert=True)
        return

    booking_id = await db.create_booking(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        day=selected,
        time_slot=time_slot,
    )

    job_id = reminder_scheduler.schedule_reminder(
        booking_id=booking_id,
        user_id=user.id,
        day=selected,
        time_slot=time_slot,
    )
    if job_id:
        await db.update_booking_reminder_job(booking_id, job_id)

    await notify_admin(
        callback.bot,
        format_admin_notify(
            booking_id,
            user.id,
            user.username,
            user.full_name,
            selected,
            time_slot,
        ),
    )

    await update_channel_schedule(callback.bot)

    await state.clear()
    is_admin = user.id == settings.admin_id
    await callback.message.edit_text(
        format_booking_success(selected, time_slot),
        reply_markup=main_menu_keyboard(is_admin, has_booking=True),
    )
    await callback.answer("Запись создана! 💕")


@router.callback_query(F.data == "book:cancel")
async def book_cancel(
    callback: CallbackQuery,
    reminder_scheduler: ReminderScheduler,
) -> None:
    """Отмена записи пользователем."""
    booking = await db.get_active_booking_by_user(callback.from_user.id)
    if not booking:
        await callback.answer("Активной записи нет.", show_alert=True)
        return

    reminder_scheduler.cancel_reminder(booking["id"])
    cancelled = await db.cancel_booking(booking["id"])
    await update_channel_schedule(callback.bot)

    if cancelled:
        day = date.fromisoformat(cancelled["date"])
        await notify_admin(
            callback.bot,
            format_admin_cancel_notify(
                booking_id=cancelled["id"],
                user_id=cancelled["user_id"],
                username=cancelled.get("username"),
                full_name=cancelled.get("full_name"),
                day=day,
                time_slot=cancelled["time"],
                cancelled_at=cancelled.get("cancelled_at"),
            ),
        )

    is_admin = callback.from_user.id == settings.admin_id
    await callback.message.edit_text(
        "<b>Запись отменена</b>\n\n"
        "Надеюсь увидеть тебя в другой день! 💫",
        reply_markup=main_menu_keyboard(is_admin, has_booking=False),
    )
    await callback.answer()


@router.callback_query(F.data.endswith(":ignore"))
async def calendar_ignore(callback: CallbackQuery) -> None:
    await callback.answer()
