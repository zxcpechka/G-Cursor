"""
Inline-календарь для выбора даты.
"""

from calendar import monthrange
from datetime import date, timedelta

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import settings

MONTH_NAMES = (
    "",
    "Январь",
    "Февраль",
    "Март",
    "Апрель",
    "Май",
    "Июнь",
    "Июль",
    "Август",
    "Сентябрь",
    "Октябрь",
    "Ноябрь",
    "Декабрь",
)

WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


async def build_calendar_keyboard(
    year: int,
    month: int,
    available_dates: set[date],
    min_date: date,
    max_date: date,
    callback_prefix: str = "cal",
) -> InlineKeyboardMarkup:
    """
    Построить календарь на месяц.
    Доступны только дни из available_dates в пределах [min_date, max_date].
    """
    builder = InlineKeyboardBuilder()

    # Заголовок месяца
    builder.row(
        InlineKeyboardButton(
            text=f"📅 {MONTH_NAMES[month]} {year}",
            callback_data=f"{callback_prefix}:ignore",
        )
    )

    # Дни недели
    builder.row(
        *[InlineKeyboardButton(text=d, callback_data=f"{callback_prefix}:ignore") for d in WEEKDAYS]
    )

    first_weekday, days_in_month = monthrange(year, month)
    # monthrange: понедельник = 0
    row_buttons: list[InlineKeyboardButton] = []

    # Пустые ячейки до первого дня
    for _ in range(first_weekday):
        row_buttons.append(
            InlineKeyboardButton(text=" ", callback_data=f"{callback_prefix}:ignore")
        )

    for day_num in range(1, days_in_month + 1):
        current = date(year, month, day_num)
        if min_date <= current <= max_date and current in available_dates:
            row_buttons.append(
                InlineKeyboardButton(
                    text=str(day_num),
                    callback_data=f"{callback_prefix}:day:{current.isoformat()}",
                )
            )
        else:
            row_buttons.append(
                InlineKeyboardButton(text="·", callback_data=f"{callback_prefix}:ignore")
            )

        if len(row_buttons) == 7:
            builder.row(*row_buttons)
            row_buttons = []

    if row_buttons:
        while len(row_buttons) < 7:
            row_buttons.append(
                InlineKeyboardButton(text=" ", callback_data=f"{callback_prefix}:ignore")
            )
        builder.row(*row_buttons)

    # Навигация по месяцам
    prev_month = date(year, month, 1) - timedelta(days=1)
    next_month = date(year, month, monthrange(year, month)[1]) + timedelta(days=1)

    nav_buttons = []
    prev_first = date(prev_month.year, prev_month.month, 1)
    if prev_first >= date(min_date.year, min_date.month, 1):
        nav_buttons.append(
            InlineKeyboardButton(
                text="◀️",
                callback_data=f"{callback_prefix}:nav:{prev_month.year}-{prev_month.month:02d}",
            )
        )
    nav_buttons.append(
        InlineKeyboardButton(text="🏠 Меню", callback_data="menu:main")
    )
    next_first = date(next_month.year, next_month.month, 1)
    max_first = date(max_date.year, max_date.month, 1)
    if next_first <= max_first:
        nav_buttons.append(
            InlineKeyboardButton(
                text="▶️",
                callback_data=f"{callback_prefix}:nav:{next_month.year}-{next_month.month:02d}",
            )
        )
    builder.row(*nav_buttons)

    return builder.as_markup()


def get_schedule_date_range(today: date) -> tuple[date, date]:
    """Диапазон дат расписания (сегодня + N дней)."""
    max_date = today + timedelta(days=settings.schedule_days_ahead)
    return today, max_date
