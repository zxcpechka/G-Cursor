"""
HTML-тексты сообщений бота.
"""

from datetime import date
from typing import Any

MONTH_NAMES_GENITIVE = (
    "",
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
)


def format_date_ru(d: date) -> str:
    """Дата в формате «15 июня»."""
    return f"{d.day} {MONTH_NAMES_GENITIVE[d.month]}"


def format_date_full_ru(d: date) -> str:
    """Дата в формате «15 июня 2026»."""
    return f"{d.day} {MONTH_NAMES_GENITIVE[d.month]} {d.year}"


def walk_dates_text() -> str:
    """Список дат для прогулки (июнь)."""
    lines = [f"{i} июня" for i in range(1, 31)]
    body = "\n".join(lines)
    return (
        "<b>🌸 Даты для прогулки</b>\n\n"
        f"<i>Каждый день — повод для романтики:</i>\n\n"
        f"{body}"
    )


def format_booking_confirm(day: date, time_slot: str) -> str:
    """Сообщение перед подтверждением."""
    return (
        "<b>💕 Почти готово!</b>\n\n"
        f"📅 Дата: <b>{format_date_full_ru(day)}</b>\n"
        f"🕐 Время: <b>{time_slot}</b>\n\n"
        "Ты согласна на встречу?"
    )


def format_booking_success(day: date, time_slot: str) -> str:
    return (
        "<b>✨ Запись подтверждена!</b>\n\n"
        f"Жду тебя <b>{format_date_full_ru(day)}</b> в <b>{time_slot}</b>.\n\n"
        "До встречи! 💕"
    )


def _user_line(username: str | None, full_name: str | None, user_id: int) -> str:
    uname = f"@{username}" if username else "—"
    name = full_name or "—"
    return f"👤 {name} ({uname})\n🔢 ID: <code>{user_id}</code>"


def format_admin_notify(
    booking_id: int,
    user_id: int,
    username: str | None,
    full_name: str | None,
    day: date,
    time_slot: str,
) -> str:
    return (
        "<b>📩 Новая запись на свидание</b>\n\n"
        f"🆔 Запись: <code>{booking_id}</code>\n"
        f"{_user_line(username, full_name, user_id)}\n"
        f"📅 Дата: <b>{format_date_full_ru(day)}</b>\n"
        f"🕐 Время: <b>{time_slot}</b>"
    )


def format_admin_cancel_notify(
    booking_id: int,
    user_id: int,
    username: str | None,
    full_name: str | None,
    day: date,
    time_slot: str,
    cancelled_at: str | None = None,
) -> str:
    """Уведомление админу об отмене встречи."""
    when = f"\n🕒 Отменено: <b>{cancelled_at}</b>" if cancelled_at else ""
    return (
        "<b>❌ Встреча отменена</b>\n\n"
        f"🆔 Запись: <code>{booking_id}</code>\n"
        f"{_user_line(username, full_name, user_id)}\n"
        f"📅 Была запись: <b>{format_date_full_ru(day)}</b> в <b>{time_slot}</b>"
        f"{when}"
    )


def format_cancelled_bookings_list(bookings: list[dict]) -> str:
    """Список отменённых встреч для админ-панели."""
    if not bookings:
        return (
            "<b>❌ Отменённые встречи</b>\n\n"
            "<i>Отменённых записей пока нет.</i>"
        )
    lines = ["<b>❌ Отменённые встречи</b>\n", "<i>Последние 20 отмен:</i>\n"]
    for b in bookings:
        d = date.fromisoformat(b["date"])
        name = b.get("full_name") or "—"
        uname = f" @{b['username']}" if b.get("username") else ""
        cancelled = b.get("cancelled_at") or "—"
        lines.append(
            f"\n🆔 <code>{b['id']}</code>\n"
            f"👤 {name}{uname}\n"
            f"📅 {format_date_full_ru(d)} в <b>{b['time']}</b>\n"
            f"🕒 {cancelled}"
        )
    return "\n".join(lines)


def format_schedule_channel(bookings: list[dict[str, Any]]) -> str:
    """Расписание для Telegram-канала."""
    if not bookings:
        return (
            "<b>📅 Расписание встреч</b>\n\n"
            "<i>Пока нет активных записей.</i>"
        )

    lines = ["<b>📅 Расписание встреч</b>\n"]
    for b in bookings:
        d = date.fromisoformat(b["date"])
        name = b.get("full_name") or "Гость"
        lines.append(
            f"• <b>{format_date_ru(d)}</b> в <b>{b['time']}</b> — {name}"
        )
    return "\n".join(lines)


def format_user_booking(day: date, time_slot: str) -> str:
    return (
        "<b>📌 Твоя запись</b>\n\n"
        f"📅 {format_date_full_ru(day)}\n"
        f"🕐 {time_slot}\n\n"
        "Нажми кнопку ниже, чтобы отменить."
    )


def reminder_text(time_slot: str) -> str:
    return (
        f"Напоминаем, что у нас завтра встреча {time_slot}.\n"
        "Жду тебя ❤️"
    )
