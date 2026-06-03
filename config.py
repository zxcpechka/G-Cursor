"""
Глобальные настройки бота.
Все секреты — только из переменных окружения (.env).
"""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    """Настройки приложения."""

    # Токен бота от @BotFather
    bot_token: str = os.getenv("BOT_TOKEN", "")

    # Telegram ID администратора (владельца бота)
    admin_id: int = int(os.getenv("ADMIN_ID") or "0")

    # ID или @username канала для публикации расписания
    channel_id: str = os.getenv("CHANNEL_ID", "")

    # Прокси для доступа к Telegram API (если api.telegram.org недоступен)
    # Примеры: socks5://127.0.0.1:1080  http://127.0.0.1:8080
    proxy_url: str = os.getenv("PROXY_URL", "")

    # Путь к файлу SQLite
    db_path: str = os.getenv("DB_PATH", "database/date_bot.db")

    # Часовой пояс для дат и напоминаний
    timezone: str = os.getenv("TIMEZONE", "Europe/Moscow")

    # Доступные слоты времени (через запятую)
    time_slots: list[str] = field(default_factory=list)

    # Сколько дней вперёд показывать календарь
    schedule_days_ahead: int = int(os.getenv("SCHEDULE_DAYS_AHEAD", "30"))

    def __post_init__(self) -> None:
        slots_raw = os.getenv(
            "TIME_SLOTS",
            "10:00,11:00,12:00,14:00,16:00,18:00,19:00,20:00",
        )
        self.time_slots = [s.strip() for s in slots_raw.split(",") if s.strip()]


settings = Settings()
