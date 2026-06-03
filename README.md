# Telegram-бот «Приглашение на свидание»

Бот на **aiogram 3** и **SQLite** для записи на встречу: календарь, выбор времени, подтверждение, напоминания за 24 часа, админ-панель и публикация расписания в канал.

## Структура проекта

```
.
├── bot.py                  # Точка входа
├── config.py               # Настройки из .env
├── requirements.txt
├── .env.example
├── database/
│   ├── __init__.py
│   └── db.py               # SQLite: дни, записи, настройки
├── handlers/
│   ├── __init__.py
│   ├── start.py            # /start, главное меню
│   ├── booking.py          # Запись и отмена (FSM)
│   ├── admin.py            # Админ-панель (FSM)
│   └── walk_dates.py       # «Даты для прогулки»
├── keyboards/
│   ├── __init__.py
│   ├── calendar.py         # Inline-календарь
│   └── inline.py           # Кнопки меню
├── states/
│   ├── __init__.py
│   └── fsm.py              # FSM-состояния
└── utils/
    ├── scheduler.py        # APScheduler: напоминания
    ├── channel.py          # Обновление канала
    └── texts.py            # HTML-тексты
```

## Установка зависимостей

```bash
# 1. Создать виртуальное окружение (рекомендуется)
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

# 2. Установить пакеты
pip install -r requirements.txt
```

## Настройка

1. Скопируйте `.env.example` в `.env`:
   ```bash
   copy .env.example .env
   ```
2. Заполните переменные:
   - `BOT_TOKEN` — токен от [@BotFather](https://t.me/BotFather)
   - `ADMIN_ID` — ваш Telegram ID ([@userinfobot](https://t.me/userinfobot))
   - `CHANNEL_ID` — канал для расписания (бот должен быть **администратором** канала)
3. Добавьте рабочие дни через **Админ-панель** в боте.

## Запуск

```bash
python bot.py
```

## Функционал

| Возможность | Описание |
|-------------|----------|
| Запись | Календарь на месяц → время → подтверждение Да/Нет |
| Отмена | Кнопка «Отменить мою запись» |
| Даты для прогулки | Список дней июня (HTML) |
| Напоминание | За 24 ч до встречи (APScheduler), восстановление после перезапуска |
| Админ | Добавление рабочих дней, просмотр записей |
| Канал | Автообновление расписания встреч |

## Технологии

- Python 3.10+
- aiogram 3.28+
- aiosqlite
- APScheduler (AsyncIOScheduler)
- SQLite
