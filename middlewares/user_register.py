"""
Регистрация пользователя при любом обращении к боту.
"""

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from database import db


class UserRegisterMiddleware(BaseMiddleware):
    """Сохраняет user_id в БД для будущих рассылок."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user: User | None = data.get("event_from_user")
        if user and not user.is_bot:
            await db.register_user(user.id, user.username, user.full_name)
        return await handler(event, data)
