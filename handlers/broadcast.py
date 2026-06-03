"""
Рассылка сообщения всем пользователям (только админ).
"""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import db
from handlers.admin import is_admin
from keyboards.inline import admin_panel_keyboard, broadcast_confirm_keyboard
from states.fsm import AdminStates
from utils.broadcast import build_payload_from_message, send_broadcast_by_id

router = Router()


@router.callback_query(F.data == "admin:broadcast")
async def broadcast_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён.", show_alert=True)
        return

    count = await db.count_bot_users()
    await state.set_state(AdminStates.writing_broadcast)
    await callback.message.edit_text(
        "<b>📢 Рассылка всем пользователям</b>\n\n"
        f"Сейчас в базе: <b>{count}</b> чел.\n\n"
        "Отправьте <b>одно сообщение</b> — текст, фото, видео или файл.\n"
        "Его увидят все, кто хоть раз обращался к боту.\n\n"
        "<i>Для отмены: /cancel</i>",
    )
    await callback.answer()


@router.message(AdminStates.writing_broadcast, F.text == "/cancel")
async def broadcast_cancel_cmd(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer(
        "<b>Рассылка отменена</b>",
        reply_markup=admin_panel_keyboard(),
    )


@router.callback_query(F.data == "admin:broadcast:cancel")
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        return
    await state.clear()
    await callback.message.edit_text(
        "<b>Рассылка отменена</b>",
        reply_markup=admin_panel_keyboard(),
    )
    await callback.answer()


@router.message(AdminStates.writing_broadcast)
async def broadcast_preview(message: Message, state: FSMContext) -> None:
    """Получить сообщение от админа и показать превью."""
    if not is_admin(message.from_user.id):
        return

    if not (
        message.text
        or message.photo
        or message.video
        or message.document
        or message.sticker
        or message.voice
    ):
        await message.answer(
            "Отправьте текст, фото, видео, файл или голосовое.\n"
            "Или /cancel для отмены."
        )
        return

    payload = build_payload_from_message(message)
    await state.update_data(
        broadcast_chat_id=message.chat.id,
        broadcast_message_id=message.message_id,
        broadcast_payload=payload,
    )

    count = await db.count_bot_users()
    await message.answer(
        f"<b>📢 Превью рассылки</b>\n\n"
        f"Получателей: <b>{count}</b> чел.\n"
        "Сообщение выше — пример (у пользователей будет заголовок "
        "«📢 Сообщение»).\n\n"
        "Отправить всем?",
        reply_markup=broadcast_confirm_keyboard(),
    )


@router.callback_query(F.data == "admin:broadcast:confirm")
async def broadcast_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        return

    data = await state.get_data()
    chat_id = data.get("broadcast_chat_id")
    message_id = data.get("broadcast_message_id")
    payload = data.get("broadcast_payload")
    if not chat_id or not message_id or not payload:
        await callback.answer("Сначала отправьте сообщение для рассылки.", show_alert=True)
        return

    await callback.message.edit_text("<b>⏳ Рассылка...</b> Подождите.")
    await callback.answer()

    result = await send_broadcast_by_id(
        callback.bot,
        int(chat_id),
        int(message_id),
        payload,
    )

    await state.clear()
    await callback.message.edit_text(
        "<b>✅ Рассылка завершена</b>\n\n"
        f"📤 Доставлено: <b>{result.sent}</b>\n"
        f"🚫 Заблокировали бота: <b>{result.blocked}</b>\n"
        f"⚠️ Ошибки: <b>{result.failed}</b>\n"
        f"👥 Всего в базе: <b>{result.total}</b>",
        reply_markup=admin_panel_keyboard(),
    )
