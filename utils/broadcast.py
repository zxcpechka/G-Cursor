"""
Рассылка сообщения всем пользователям бота.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from config import settings
from database import db

logger = logging.getLogger(__name__)

BROADCAST_HEADER = "<b>📢 Сообщение</b>\n\n"
DELAY_SEC = 0.05


@dataclass
class BroadcastResult:
    sent: int = 0
    failed: int = 0
    blocked: int = 0
    total: int = 0


async def send_broadcast_by_id(
    bot: Bot,
    from_chat_id: int,
    message_id: int,
    payload: dict[str, Any],
) -> BroadcastResult:
    """
    Разослать сообщение всем пользователям.
    payload — данные из FSM (тип и содержимое сообщения админа).
    """
    user_ids = await db.get_broadcast_user_ids()
    result = BroadcastResult(total=len(user_ids))

    for user_id in user_ids:
        if user_id == settings.admin_id:
            continue
        try:
            await _send_payload(bot, user_id, from_chat_id, message_id, payload)
            result.sent += 1
        except TelegramForbiddenError:
            await db.mark_user_blocked(user_id)
            result.blocked += 1
        except TelegramBadRequest as exc:
            logger.warning("Рассылка user_id=%s: %s", user_id, exc)
            result.failed += 1
        except Exception as exc:
            logger.error("Рассылка user_id=%s: %s", user_id, exc)
            result.failed += 1
        await asyncio.sleep(DELAY_SEC)

    return result


async def _send_payload(
    bot: Bot,
    user_id: int,
    from_chat_id: int,
    message_id: int,
    payload: dict[str, Any],
) -> None:
    """Отправить одному пользователю."""
    msg_type = payload.get("type", "copy")

    if msg_type == "text":
        await bot.send_message(
            user_id,
            f"{BROADCAST_HEADER}{payload['html_text']}",
        )
        return

    if msg_type == "photo":
        cap = payload.get("caption_html") or ""
        caption = f"{BROADCAST_HEADER}{cap}" if cap else BROADCAST_HEADER.strip()
        await bot.send_photo(user_id, payload["file_id"], caption=caption)
        return

    if msg_type == "video":
        cap = payload.get("caption_html") or ""
        caption = f"{BROADCAST_HEADER}{cap}" if cap else BROADCAST_HEADER.strip()
        await bot.send_video(user_id, payload["file_id"], caption=caption)
        return

    if msg_type == "document":
        cap = payload.get("caption_html") or ""
        caption = f"{BROADCAST_HEADER}{cap}" if cap else BROADCAST_HEADER.strip()
        await bot.send_document(user_id, payload["file_id"], caption=caption)
        return

    # Любой другой тип — заголовок + копия оригинала
    await bot.send_message(user_id, BROADCAST_HEADER.strip())
    await bot.copy_message(
        chat_id=user_id,
        from_chat_id=from_chat_id,
        message_id=message_id,
    )


def build_payload_from_message(message) -> dict[str, Any]:
    """Подготовить данные сообщения для рассылки."""
    if message.text:
        return {"type": "text", "html_text": message.html_text}

    if message.photo:
        return {
            "type": "photo",
            "file_id": message.photo[-1].file_id,
            "caption_html": message.html_text if message.caption else "",
        }

    if message.video:
        return {
            "type": "video",
            "file_id": message.video.file_id,
            "caption_html": message.html_text if message.caption else "",
        }

    if message.document:
        return {
            "type": "document",
            "file_id": message.document.file_id,
            "caption_html": message.html_text if message.caption else "",
        }

    return {"type": "copy"}
