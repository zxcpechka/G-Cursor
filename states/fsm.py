"""
Состояния FSM для пользователя и администратора.
"""

from aiogram.fsm.state import State, StatesGroup


class BookingStates(StatesGroup):
    """Сценарий записи на свидание."""

    choosing_date = State()
    choosing_time = State()
    confirming = State()


class AdminStates(StatesGroup):
    """Сценарий админ-панели."""

    choosing_work_day = State()
    writing_broadcast = State()
