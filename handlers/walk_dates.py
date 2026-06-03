"""
Кнопка «Даты для прогулки».
"""

from aiogram import F, Router
from aiogram.types import CallbackQuery

from keyboards.inline import back_to_menu_keyboard
from utils.texts import walk_dates_text

router = Router()


@router.callback_query(F.data == "walk:dates")
async def show_walk_dates(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        walk_dates_text(),
        reply_markup=back_to_menu_keyboard(),
    )
    await callback.answer()
