"""
Команда /start и главное меню.
"""

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import settings
from database import db
from keyboards.inline import main_menu_keyboard

router = Router()


WELCOME_TEXT = (
    "<b>💕 Добро пожаловать!</b>\n\n"
    "Этот бот поможет выбрать удобный день и время для нашей встречи.\n\n"
    "Выбери действие в меню ниже:"
)


async def _send_main_menu(target: Message, user_id: int) -> None:
    """Показать главное меню."""
    has_booking = await db.get_active_booking_by_user(user_id) is not None
    is_admin = user_id == settings.admin_id
    await target.answer(
        WELCOME_TEXT,
        reply_markup=main_menu_keyboard(is_admin, has_booking),
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _send_main_menu(message, message.from_user.id)


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _send_main_menu(message, message.from_user.id)


@router.callback_query(F.data == "menu:main")
async def callback_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    has_booking = await db.get_active_booking_by_user(callback.from_user.id) is not None
    is_admin = callback.from_user.id == settings.admin_id
    await callback.message.edit_text(
        WELCOME_TEXT,
        reply_markup=main_menu_keyboard(is_admin, has_booking),
    )
    await callback.answer()
