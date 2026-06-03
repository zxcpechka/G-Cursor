"""
Публикация и обновление расписания в Telegram-канале.
"""

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from config import settings
from database import db
from utils.texts import format_schedule_channel

logger = logging.getLogger(__name__)

CHANNEL_MSG_KEY = "channel_schedule_message_id"


async def update_channel_schedule(bot: Bot) -> None:
    """Отправить или отредактировать сообщение с расписанием в канале."""
    if not settings.channel_id:
        return

    bookings = await db.get_all_active_bookings()
    text = format_schedule_channel(bookings)
    msg_id_str = await db.get_setting(CHANNEL_MSG_KEY)

    try:
        if msg_id_str:
            await bot.edit_message_text(
                text=text,
                chat_id=settings.channel_id,
                message_id=int(msg_id_str),
            )
        else:
            msg = await bot.send_message(settings.channel_id, text)
            await db.set_setting(CHANNEL_MSG_KEY, str(msg.message_id))
    except TelegramBadRequest as exc:
        # Сообщение удалено — отправляем новое
        if "message to edit not found" in str(exc).lower() or "message can't be edited" in str(exc).lower():
            msg = await bot.send_message(settings.channel_id, text)
            await db.set_setting(CHANNEL_MSG_KEY, str(msg.message_id))
        else:
            logger.error("Ошибка обновления канала: %s", exc)
    except Exception as exc:
        logger.error("Не удалось обновить канал: %s", exc)
