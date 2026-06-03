"""
Работа с SQLite: рабочие дни, записи, настройки канала.
"""

from __future__ import annotations

import aiosqlite
from datetime import date, datetime
from typing import Any

from config import settings


async def init_db() -> None:
    """Создать таблицы при первом запуске."""
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        await db.executescript(
            """
            CREATE TABLE IF NOT EXISTS working_days (
                date TEXT PRIMARY KEY
            );

            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                full_name TEXT,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                reminder_job_id TEXT
            );

            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_bookings_user
                ON bookings(user_id, status);
            CREATE INDEX IF NOT EXISTS idx_bookings_date_time
                ON bookings(date, time, status);

            CREATE TABLE IF NOT EXISTS bot_users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                is_blocked INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        await db.commit()
    await _migrate_bookings_columns()
    await sync_users_from_bookings()


async def _migrate_bookings_columns() -> None:
    """Добавить новые колонки в существующую БД."""
    async with aiosqlite.connect(settings.db_path) as db:
        cursor = await db.execute("PRAGMA table_info(bookings)")
        columns = {row[1] for row in await cursor.fetchall()}
        if "cancelled_at" not in columns:
            await db.execute(
                "ALTER TABLE bookings ADD COLUMN cancelled_at TEXT"
            )
            await db.commit()


# --- Рабочие дни ---


async def add_working_day(day: date) -> bool:
    """Добавить рабочий день. False, если уже есть."""
    async with aiosqlite.connect(settings.db_path) as db:
        try:
            await db.execute(
                "INSERT INTO working_days (date) VALUES (?)",
                (day.isoformat(),),
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False


async def remove_working_day(day: date) -> None:
    """Удалить рабочий день."""
    async with aiosqlite.connect(settings.db_path) as db:
        await db.execute(
            "DELETE FROM working_days WHERE date = ?",
            (day.isoformat(),),
        )
        await db.commit()


async def is_working_day(day: date) -> bool:
    """Проверить, является ли день рабочим."""
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT 1 FROM working_days WHERE date = ?",
            (day.isoformat(),),
        )
        return await cursor.fetchone() is not None


async def get_working_days_between(start: date, end: date) -> list[date]:
    """Список рабочих дней в диапазоне."""
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT date FROM working_days
            WHERE date >= ? AND date <= ?
            ORDER BY date
            """,
            (start.isoformat(), end.isoformat()),
        )
        rows = await cursor.fetchall()
    return [date.fromisoformat(r["date"]) for r in rows]


# --- Записи ---


async def create_booking(
    user_id: int,
    username: str | None,
    full_name: str | None,
    day: date,
    time_slot: str,
    reminder_job_id: str | None = None,
) -> int:
    """Создать запись, вернуть id."""
    async with aiosqlite.connect(settings.db_path) as db:
        cursor = await db.execute(
            """
            INSERT INTO bookings
                (user_id, username, full_name, date, time, status, created_at, reminder_job_id)
            VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
            """,
            (
                user_id,
                username,
                full_name,
                day.isoformat(),
                time_slot,
                datetime.now().isoformat(timespec="seconds"),
                reminder_job_id,
            ),
        )
        await db.commit()
        return cursor.lastrowid  # type: ignore[return-value]


async def update_booking_reminder_job(booking_id: int, job_id: str | None) -> None:
    """Сохранить id задачи напоминания."""
    async with aiosqlite.connect(settings.db_path) as db:
        await db.execute(
            "UPDATE bookings SET reminder_job_id = ? WHERE id = ?",
            (job_id, booking_id),
        )
        await db.commit()


async def cancel_booking(booking_id: int) -> dict[str, Any] | None:
    """Отменить запись, вернуть данные записи."""
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM bookings WHERE id = ? AND status = 'active'",
            (booking_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        cancelled_at = datetime.now().strftime("%d.%m.%Y %H:%M")
        await db.execute(
            """
            UPDATE bookings
            SET status = 'cancelled',
                reminder_job_id = NULL,
                cancelled_at = ?
            WHERE id = ?
            """,
            (cancelled_at, booking_id),
        )
        await db.commit()
        result = dict(row)
        result["cancelled_at"] = cancelled_at
        return result


async def get_active_booking_by_user(user_id: int) -> dict[str, Any] | None:
    """Активная запись пользователя (одна на пользователя)."""
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT * FROM bookings
            WHERE user_id = ? AND status = 'active'
            ORDER BY date, time
            LIMIT 1
            """,
            (user_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def is_slot_taken(day: date, time_slot: str) -> bool:
    """Занят ли слот."""
    async with aiosqlite.connect(settings.db_path) as db:
        cursor = await db.execute(
            """
            SELECT 1 FROM bookings
            WHERE date = ? AND time = ? AND status = 'active'
            """,
            (day.isoformat(), time_slot),
        )
        return await cursor.fetchone() is not None


async def get_available_slots(day: date) -> list[str]:
    """Свободные слоты на дату."""
    result = []
    for slot in settings.time_slots:
        if not await is_slot_taken(day, slot):
            result.append(slot)
    return result


async def get_cancelled_bookings(limit: int = 20) -> list[dict[str, Any]]:
    """Последние отменённые записи (для админ-панели)."""
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT * FROM bookings
            WHERE status = 'cancelled'
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_all_active_bookings() -> list[dict[str, Any]]:
    """Все активные записи для расписания в канале."""
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT * FROM bookings
            WHERE status = 'active'
            ORDER BY date, time
            """
        )
        rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_bookings_for_reminder_restore() -> list[dict[str, Any]]:
    """Активные записи с запланированным напоминанием."""
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT * FROM bookings
            WHERE status = 'active' AND reminder_job_id IS NOT NULL
            """
        )
        rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_booking_by_id(booking_id: int) -> dict[str, Any] | None:
    """Запись по id."""
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM bookings WHERE id = ?",
            (booking_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


# --- Пользователи бота (для рассылки) ---


async def register_user(
    user_id: int,
    username: str | None = None,
    full_name: str | None = None,
) -> None:
    """Сохранить или обновить пользователя."""
    now = datetime.now().isoformat(timespec="seconds")
    async with aiosqlite.connect(settings.db_path) as db:
        await db.execute(
            """
            INSERT INTO bot_users (user_id, username, full_name, first_seen, last_seen, is_blocked)
            VALUES (?, ?, ?, ?, ?, 0)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name,
                last_seen = excluded.last_seen,
                is_blocked = 0
            """,
            (user_id, username, full_name, now, now),
        )
        await db.commit()


async def mark_user_blocked(user_id: int) -> None:
    """Пометить пользователя (заблокировал бота)."""
    async with aiosqlite.connect(settings.db_path) as db:
        await db.execute(
            "UPDATE bot_users SET is_blocked = 1 WHERE user_id = ?",
            (user_id,),
        )
        await db.commit()


async def get_broadcast_user_ids() -> list[int]:
    """ID всех пользователей для рассылки (кроме заблокировавших бота)."""
    async with aiosqlite.connect(settings.db_path) as db:
        cursor = await db.execute(
            "SELECT user_id FROM bot_users WHERE is_blocked = 0"
        )
        rows = await cursor.fetchall()
    return [row[0] for row in rows]


async def count_bot_users() -> int:
    async with aiosqlite.connect(settings.db_path) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM bot_users WHERE is_blocked = 0"
        )
        row = await cursor.fetchone()
    return row[0] if row else 0


async def sync_users_from_bookings() -> None:
    """Импортировать пользователей из таблицы записей."""
    async with aiosqlite.connect(settings.db_path) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO bot_users (user_id, username, full_name, first_seen, last_seen)
            SELECT DISTINCT user_id, username, full_name, created_at, created_at
            FROM bookings
            """
        )
        await db.commit()


# --- Настройки бота (id сообщения в канале) ---


async def get_setting(key: str) -> str | None:
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT value FROM bot_settings WHERE key = ?",
            (key,),
        )
        row = await cursor.fetchone()
        return row["value"] if row else None


async def set_setting(key: str, value: str) -> None:
    async with aiosqlite.connect(settings.db_path) as db:
        await db.execute(
            """
            INSERT INTO bot_settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )
        await db.commit()
