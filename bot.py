"""
Точка входа: Telegram-бот для записи на свидание.
"""

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramNetworkError
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database import db
from handlers import admin, booking, broadcast, start, walk_dates
from middlewares.scheduler import SchedulerMiddleware
from middlewares.user_register import UserRegisterMiddleware
from utils.scheduler import ReminderScheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_bot() -> Bot:
    """Создать Bot с увеличенным таймаутом и опциональным прокси."""
    session_kwargs: dict = {"timeout": 120}
    if settings.proxy_url:
        session_kwargs["proxy"] = settings.proxy_url
        logger.info("Используется прокси для Telegram API.")
    session = AiohttpSession(**session_kwargs)
    return Bot(
        token=settings.bot_token,
        session=session,
        default=DefaultBotProperties(parse_mode="HTML"),
    )


def setup_dispatcher() -> Dispatcher:
    """Создать Dispatcher и подключить роутеры."""
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start.router)
    dp.include_router(walk_dates.router)
    dp.include_router(booking.router)
    dp.include_router(admin.router)
    dp.include_router(broadcast.router)
    return dp


async def init_local_services(reminder_scheduler: ReminderScheduler) -> None:
    """Локальная инициализация без обращения к Telegram API."""
    os.makedirs(os.path.dirname(settings.db_path) or ".", exist_ok=True)
    await db.init_db()
    logger.info("База данных инициализирована.")
    reminder_scheduler.start()
    await reminder_scheduler.restore_from_db()


async def check_telegram_connection(bot: Bot) -> bool:
    """Проверить доступность api.telegram.org."""
    try:
        me = await bot.get_me()
        logger.info("Подключение OK. Бот: @%s", me.username)
        return True
    except TelegramNetworkError as exc:
        logger.error(
            "Нет связи с api.telegram.org: %s\n"
            "Проверьте интернет, VPN или укажите PROXY_URL в .env "
            "(socks5://127.0.0.1:1080 или http://127.0.0.1:8080).",
            exc,
        )
        return False


async def main() -> None:
    if not settings.bot_token:
        raise RuntimeError(
            "BOT_TOKEN не задан. Создайте файл .env (см. .env.example)."
        )
    if not settings.admin_id:
        logger.warning(
            "ADMIN_ID не задан в .env — админ-панель недоступна. "
            "Узнайте ID в @userinfobot и добавьте строку ADMIN_ID=ваш_id"
        )

    bot = create_bot()
    dp = setup_dispatcher()
    reminder_scheduler = ReminderScheduler(bot)
    dp.update.middleware(UserRegisterMiddleware())
    dp.update.middleware(SchedulerMiddleware(reminder_scheduler))

    @dp.shutdown()
    async def _on_shutdown() -> None:
        reminder_scheduler.shutdown()
        logger.info("Планировщик остановлен.")

    await init_local_services(reminder_scheduler)

    logger.info("Запуск polling...")
    if not await check_telegram_connection(bot):
        await bot.session.close()
        raise SystemExit(1)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")
