"""
Уведомления администратору в личные сообщения.
"""

import logging

from aiogram import Bot

from config import settings

logger = logging.getLogger(__name__)


async def notify_admin(bot: Bot, text: str) -> None:
    """Отправить HTML-сообщение администратору."""
    if not settings.admin_id:
        return
    try:
        await bot.send_message(settings.admin_id, text)
    except Exception as exc:
        logger.error("Не удалось уведомить администратора: %s", exc)
