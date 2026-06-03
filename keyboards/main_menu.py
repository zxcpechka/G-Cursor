from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


# Главное меню с одной кнопкой "Начать"
main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Начать")],
    ],
    resize_keyboard=True,
    input_field_placeholder="Нажмите «Начать», чтобы сгенерировать текст песни",
)


def genre_inline_keyboard() -> InlineKeyboardMarkup:
    """
    Инлайн‑клавиатура выбора жанра.
    Обязательная по ТЗ кнопка "Рэп" присутствует.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Рэп", callback_data="genre_rap"),
            ],
            [
                InlineKeyboardButton(text="Поп", callback_data="genre_pop"),
                InlineKeyboardButton(text="Рок", callback_data="genre_rock"),
            ],
            [
                InlineKeyboardButton(text="R&B", callback_data="genre_rnb"),
                InlineKeyboardButton(text="Электроника", callback_data="genre_electro"),
            ],
        ]
    )


def difficulty_inline_keyboard() -> InlineKeyboardMarkup:
    """
    Инлайн‑клавиатура выбора сложности текста.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Лёгкая", callback_data="diff_easy"),
                InlineKeyboardButton(text="Средняя", callback_data="diff_medium"),
                InlineKeyboardButton(text="Сложная", callback_data="diff_hard"),
            ]
        ]
    )


def save_or_discard_keyboard() -> InlineKeyboardMarkup:
    """
    Инлайн‑клавиатура после генерации текста:
    сохранить или не сохранять.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💾 Сохранить", callback_data="song_save"
                ),
                InlineKeyboardButton(
                    text="❌ Не сохранять", callback_data="song_discard"
                ),
            ]
        ]
    )


def my_songs_keyboard() -> InlineKeyboardMarkup:
    """
    Инлайн‑клавиатура для просмотра списка сохранённых песен.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📜 Мои тексты", callback_data="my_songs_list"
                )
            ]
        ]
    )


def delete_song_keyboard(song_id: int) -> InlineKeyboardMarkup:
    """
    Инлайн‑клавиатура удаления конкретной песни.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗑 Удалить этот текст",
                    callback_data=f"delete_song_{song_id}",
                )
            ]
        ]
    )

