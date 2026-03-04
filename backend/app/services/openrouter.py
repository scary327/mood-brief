import base64
import json
import logging

import httpx

from app.config import settings
from app.schemas import ImageTagSet

logger = logging.getLogger(__name__)

VISION_PROMPT = """Role: Ты — экспертный арт-директор и системный аналитик в дизайне.
Task: Твоя задача — провести глубокую деконструкцию загруженного изображения и превратить его в массив технических тегов для формирования ТЗ.

Output Format (JSON strictly):
{
  "style": ["название стиля", "эпоха", "настроение"],
  "color_palette": ["hex-коды", "соотношение цветов", "тип гармонии"],
  "typography": ["тип шрифта: гротеск/антиква", "характер начертания", "иерархия"],
  "composition": ["сетка", "баланс", "фокусные точки", "использование негативного пространства"],
  "ui_elements": ["формы кнопок", "радиусы скругления", "стиль иконок", "типы теней/градиентов"],
  "visual_hooks": ["необычные графические приемы", "текстуры", "эффекты"]
}

Constraint: Будь максимально специфичным. Вместо "синий" пиши "глубокий кобальтовый #0047AB". Вместо "современный стиль" пиши "швейцарский минимализм с элементами нео-брутализма". Не упускай ни одной мелкой детали: шум, зернистость, толщина линий, тип разделителей.

IMPORTANT: Return ONLY the raw JSON object — no markdown, no code fences, no commentary."""


async def deconstruct_image_to_tags(image_bytes: bytes, filename: str = "") -> ImageTagSet:
    """Send an image to OpenRouter Vision model and parse structured tags."""
    b64 = base64.b64encode(image_bytes).decode("utf-8")

    # Detect mime type from first bytes
    mime = "image/jpeg"
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        mime = "image/png"
    elif image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        mime = "image/webp"

    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": VISION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime};base64,{b64}",
                        },
                    },
                ],
            }
        ],
        "max_tokens": 1024,
        "temperature": 0.2,
    }

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://moodbrief.app",
        "X-Title": "MoodBrief",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{settings.OPENROUTER_BASE_URL}/chat/completions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

    raw_text = data["choices"][0]["message"]["content"].strip()

    # Strip possible markdown code fences
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1]  # remove first ``` line
        if raw_text.endswith("```"):
            raw_text = raw_text[: -len("```")]
        raw_text = raw_text.strip()

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        logger.error("Failed to parse Vision response: %s", raw_text[:500])
        parsed = {}

    return ImageTagSet(
        style=parsed.get("style", []),
        color_palette=parsed.get("color_palette", []),
        typography=parsed.get("typography", []),
        composition=parsed.get("composition", []),
        ui_elements=parsed.get("ui_elements", []),
        visual_hooks=parsed.get("visual_hooks", []),
        filename=filename,
    )
