"""
Передача ReminderScheduler в обработчики через data.
"""

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from utils.scheduler import ReminderScheduler


class SchedulerMiddleware(BaseMiddleware):
    def __init__(self, reminder_scheduler: ReminderScheduler) -> None:
        self.reminder_scheduler = reminder_scheduler

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["reminder_scheduler"] = self.reminder_scheduler
        return await handler(event, data)
