import base64
import json
import logging

import httpx
from fastapi import HTTPException

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

Constraint: Будь максимально специфичным. Максимум 10 элементов в каждом списке. Не повторяйся. Если видишь много похожих цветов, объедини их в один.
      
IMPORTANT: Верни ТОЛЬКО чистый объект JSON — без markdown блоков (```json ... ```), без вводного текста и комментариев. Твой ответ должен начинаться с { и заканчиваться на }. """


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
        "max_tokens": 2048,
        "temperature": 0.1,
    }


    if not settings.OPENROUTER_API_KEY:
        logger.error("OPENROUTER_API_KEY is not set!")
        # We don't raise here to allow the app to start, but the request will fail

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.OPENROUTER_REFERER,
        "X-Title": settings.OPENROUTER_TITLE,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(
                f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                json=payload,
                headers=headers,
            )
            if resp.status_code == 403:
                error_data = resp.json().get("error", {})
                error_msg = error_data.get("message", "OpenRouter API key or Referer rejected")
                logger.error("OpenRouter 403 Forbidden: %s", error_msg)
                raise HTTPException(status_code=403, detail=f"OpenRouter: {error_msg}")

            
            resp.raise_for_status()
            data = resp.json()
        except HTTPException:
            # Re-raise FastAPIs HTTPException as-is
            raise
        except httpx.HTTPStatusError as e:
            logger.error("OpenRouter API error: %s", e.response.text)
            raise HTTPException(status_code=e.response.status_code, detail=f"OpenRouter error: {e.response.text}")
        except httpx.ConnectTimeout:
            logger.error("Timeout connecting to OpenRouter")
            raise HTTPException(status_code=504, detail="OpenRouter connection timed out")
        except Exception as e:
            logger.exception("Connection error to OpenRouter: %r", e)
            raise HTTPException(status_code=500, detail=f"Failed to connect to OpenRouter: {type(e).__name__}")



    raw_text = data["choices"][0]["message"]["content"].strip()


    # Robust JSON extraction
    try:
        # Find first { and last }
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start != -1 and end != -1:
            raw_text = raw_text[start : end + 1]
    except Exception:
        pass

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
