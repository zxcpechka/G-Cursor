"""
Inline-клавиатуры главного меню и подтверждения.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import settings


def main_menu_keyboard(is_admin: bool, has_booking: bool) -> InlineKeyboardMarkup:
    """Главное меню."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="💕 Записаться на свидание",
            callback_data="book:start",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🌸 Даты для прогулки",
            callback_data="walk:dates",
        )
    )
    if has_booking:
        builder.row(
            InlineKeyboardButton(
                text="❌ Отменить мою запись",
                callback_data="book:cancel",
            )
        )
    if is_admin:
        builder.row(
            InlineKeyboardButton(
                text="⚙️ Админ-панель",
                callback_data="admin:panel",
            )
        )
    return builder.as_markup()


def time_slots_keyboard(slots: list[str], prefix: str = "book:time") -> InlineKeyboardMarkup:
    """Кнопки выбора времени."""
    builder = InlineKeyboardBuilder()
    for slot in slots:
        builder.add(
            InlineKeyboardButton(
                text=f"🕐 {slot}",
                callback_data=f"{prefix}:{slot}",
            )
        )
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="book:back_to_calendar"),
        InlineKeyboardButton(text="🏠 В меню", callback_data="menu:main"),
    )
    return builder.as_markup()


def confirm_keyboard() -> InlineKeyboardMarkup:
    """Подтверждение встречи."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да", callback_data="book:confirm:yes"),
        InlineKeyboardButton(text="❌ Нет", callback_data="book:confirm:no"),
    )
    return builder.as_markup()


def admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Меню администратора."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="➕ Добавить рабочий день",
            callback_data="admin:add_day",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📋 Активные записи",
            callback_data="admin:bookings",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Отменённые встречи",
            callback_data="admin:cancelled",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📢 Сообщение всем",
            callback_data="admin:broadcast",
        )
    )
    builder.row(
        InlineKeyboardButton(text="🏠 В меню", callback_data="menu:main"),
    )
    return builder.as_markup()


def broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """Подтверждение рассылки."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Отправить всем",
            callback_data="admin:broadcast:confirm",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="admin:broadcast:cancel",
        )
    )
    return builder.as_markup()


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏠 В меню", callback_data="menu:main"))
    return builder.as_markup()
