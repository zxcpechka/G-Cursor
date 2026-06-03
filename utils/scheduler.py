"""
Планировщик напоминаний за 24 часа до встречи (APScheduler).
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from config import settings
from database import db
from utils.texts import reminder_text

logger = logging.getLogger(__name__)


def reminder_job_id(booking_id: int) -> str:
    return f"reminder_{booking_id}"


def parse_meeting_datetime(day: date, time_slot: str) -> datetime:
    """Собрать datetime встречи в настроенном часовом поясе."""
    hour, minute = map(int, time_slot.split(":"))
    tz = ZoneInfo(settings.timezone)
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=tz)


def get_reminder_datetime(meeting_dt: datetime) -> datetime:
    """Время отправки напоминания (за 24 часа)."""
    return meeting_dt - timedelta(hours=24)


class ReminderScheduler:
    """Обёртка над AsyncIOScheduler для напоминаний о встречах."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone=settings.timezone)

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Планировщик напоминаний запущен.")

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    async def send_reminder(self, user_id: int, time_slot: str, booking_id: int) -> None:
        """Отправить напоминание пользователю."""
        booking = await db.get_booking_by_id(booking_id)
        if not booking or booking["status"] != "active":
            logger.info("Напоминание #%s пропущено — запись неактивна.", booking_id)
            return
        try:
            await self.bot.send_message(user_id, reminder_text(time_slot))
            logger.info(
                "Напоминание отправлено user_id=%s booking_id=%s",
                user_id,
                booking_id,
            )
        except Exception as exc:
            logger.error("Ошибка отправки напоминания: %s", exc)

    def schedule_reminder(
        self,
        booking_id: int,
        user_id: int,
        day: date,
        time_slot: str,
    ) -> str | None:
        """
        Запланировать напоминание, если до встречи >= 24 часов.
        Возвращает job_id или None.
        """
        meeting_dt = parse_meeting_datetime(day, time_slot)
        reminder_dt = get_reminder_datetime(meeting_dt)
        now = datetime.now(ZoneInfo(settings.timezone))

        if reminder_dt <= now:
            logger.info(
                "Напоминание для записи #%s не создано — менее 24 ч до встречи.",
                booking_id,
            )
            return None

        job_id = reminder_job_id(booking_id)
        self.scheduler.add_job(
            self.send_reminder,
            trigger=DateTrigger(run_date=reminder_dt),
            id=job_id,
            replace_existing=True,
            kwargs={
                "user_id": user_id,
                "time_slot": time_slot,
                "booking_id": booking_id,
            },
        )
        logger.info(
            "Напоминание #%s запланировано на %s",
            booking_id,
            reminder_dt.isoformat(),
        )
        return job_id

    def cancel_reminder(self, booking_id: int) -> None:
        """Удалить задачу напоминания."""
        job_id = reminder_job_id(booking_id)
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info("Напоминание #%s отменено.", booking_id)

    async def restore_from_db(self) -> None:
        """Восстановить задачи из БД после перезапуска бота."""
        bookings = await db.get_all_active_bookings()
        now = datetime.now(ZoneInfo(settings.timezone))
        restored = 0

        for b in bookings:
            day = date.fromisoformat(b["date"])
            time_slot = b["time"]
            meeting_dt = parse_meeting_datetime(day, time_slot)
            reminder_dt = get_reminder_datetime(meeting_dt)

            if reminder_dt <= now:
                if b.get("reminder_job_id"):
                    await db.update_booking_reminder_job(b["id"], None)
                continue

            job_id = self.schedule_reminder(
                booking_id=b["id"],
                user_id=b["user_id"],
                day=day,
                time_slot=time_slot,
            )
            if job_id:
                await db.update_booking_reminder_job(b["id"], job_id)
                restored += 1

        logger.info("Восстановлено напоминаний: %s", restored)
