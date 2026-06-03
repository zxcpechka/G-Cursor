import textwrap

from openai import AsyncOpenAI

from config import settings


# Клиент OpenAI для работы с ChatGPT и другими моделями OpenAI
client = AsyncOpenAI(api_key=settings.openai_api_key)


async def generate_lyrics(
    genre: str,
    difficulty: str,
    theme: str,
    language: str = "ru",
) -> str:
    """
    Генерация текста песни с помощью ChatGPT.
    При необходимости можно расширить для использования других нейросетей.
    """
    if not settings.openai_api_key:
        # Если ключ не указан — сразу кидаем понятную ошибку
        raise RuntimeError(
            "OPENAI_API_KEY не задан. Установите его в .env или переменных окружения."
        )

    system_prompt = textwrap.dedent(
        f"""
        Ты — профессиональный автор песен и поэт‑песенник.
        Пиши тексты песен на языке: {language}.
        Жанр: {genre}.
        Сложность: {difficulty} (это отражает глубину, сложность рифм и образность).
        Структура: куплеты и припевы. Можно добавить бридж.
        Форматируй текст так, чтобы его удобно было читать в Telegram:
        — разделяй куплеты и припевы пустыми строками
        — выделяй припев словами "Припев:" перед ним
        """
    ).strip()

    user_prompt = textwrap.dedent(
        f"""
        Напиши текст песни.

        Жанр: {genre}
        Сложность: {difficulty}
        Тема / запрос пользователя: {theme}

        Не добавляй ничего лишнего вне текста песни (никаких комментариев).
        """
    ).strip()

    # Модель можно заменить на любую актуальную (например, gpt-4o, gpt-4o-mini и т.д.)
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.9,
        max_tokens=600,
    )

    text = response.choices[0].message.content or ""
    return text.strip()

