import base64
import json
import logging

import httpx
from fastapi import HTTPException

from app.config import settings

from app.schemas import ImageTagSet

logger = logging.getLogger(__name__)

VISION_PROMPT = """\
Ты — эксперт по веб-дизайну и UI/UX. Твоя задача — проанализировать переданное изображение \
(скриншот сайта, веб-приложения, мобильного приложения или мудборда) и выдать структурированные \
теги для дальнейшего описания в техническом задании.

ПРАВИЛА:
1. Анализируй ТОЛЬКО визуальные характеристики конкретного UI на изображении.
2. ЗАПРЕЩЕНО использовать термины из истории искусств: «постмодернизм», «футуризм», «конструктивизм», \
«баухаус», «эпоха», «рубеж веков» и т.п. Вместо этого используй прикладные UI-термины.
3. Цвета — только HEX-коды (взятые непосредственно с изображения).
4. Для style описывай конкретный UI-паттерн: например "dark mode", "neomorphism", "glassmorphism", \
"flat design", "brutalism", "retro terminal", "cyberpunk neon", "minimalism", "material design" и т.д.
5. Будь точным и конкретным — не обобщай сверх меры.
6. Максимум 8 элементов в каждом массиве.

ФОРМАТ ОТВЕТА (строго JSON, без markdown-обёртки):
{
  "style": ["UI-стиль (dark mode / neon / cyberpunk / glassmorphism / neumorphism и т.п.)",
            "общее настроение (агрессивный / спокойный / технологичный / премиальный / игривый)",
            "плотность интерфейса (dense / airy / balanced)"],
  "color_palette": ["#hex доминирующий фон", "#hex основной акцент", "#hex вторичный акцент",
                    "тип схемы: монохромная / комплементарная / аналоговая / триадная"],
  "typography": ["засечки/гротеск/моноширинный/рукописный", "вес: light/regular/bold/black",
                 "стиль: строгий/динамичный/геометрический/органичный",
                 "размер заголовков: крупные/средние/мелкие"],
  "composition": ["вёрстка: одноколоночная/многоколоночная/асимметричная/карточная/полноэкранная",
                  "количество колонок (если применимо)",
                  "баланс: симметричный/асимметричный",
                  "использование пространства: плотное/воздушное/с выраженными отступами"],
  "ui_elements": ["стиль кнопок: скруглённые/прямоугольные/pill-shape/ghost/outlined/solid",
                  "карточки: с тенями/без/с границей/glassmorphism",
                  "иконки: outline/filled/монохромные/цветные",
                  "поля ввода: understated/bordered/filled/floating-label",
                  "навигация: topbar/sidebar/hamburger/tabs/breadcrumbs"],
  "visual_hooks": ["свечение/neon glow", "градиенты (описать направление и цвета)",
                   "анимации (если видны)", "текстуры/шум/зернистость",
                   "нестандартные UI-приёмы (параллакс, reveal, hover-эффекты)",
                   "уникальные декоративные элементы"]
}

ВАЖНО: Верни ТОЛЬКО чистый JSON-объект. Твой ответ должен начинаться с { и заканчиваться на }.\
"""


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
        "max_tokens": 1500,
        "temperature": 0.05,
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

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(
                f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                json=payload,
                headers=headers,
            )
            if not resp.is_success:
                # Extract the actual error from OpenRouter's JSON if possible
                try:
                    err_body = resp.json()
                    err_detail = (
                        err_body.get("error", {}).get("message")
                        or err_body.get("message")
                        or resp.text[:400]
                    )
                except Exception:
                    err_detail = resp.text[:400] or f"HTTP {resp.status_code}"

                logger.error("Vision API error %s: %s", resp.status_code, err_detail)

                if resp.status_code == 400:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"Модель '{settings.OPENROUTER_MODEL}' отклонила запрос с изображением. "
                            f"Скорее всего, она не поддерживает Vision/изображения. "
                            f"Укажите в OPENROUTER_MODEL vision-модель (например openai/gpt-4o-mini). "
                            f"Детали: {err_detail}"
                        ),
                    )
                if resp.status_code == 413:
                    raise HTTPException(
                        status_code=413,
                        detail="Изображение слишком большое. Уменьшите его до 4 МБ или меньше.",
                    )
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"OpenRouter error {resp.status_code}: {err_detail}",
                )
            data = resp.json()
        except HTTPException:
            raise
        except httpx.ConnectError as e:
            logger.error("Vision ConnectError (likely model does not support images): %r", e)
            raise HTTPException(
                status_code=502,
                detail=(
                    f"Не удалось подключиться к провайдеру для модели '{settings.OPENROUTER_MODEL}'. "
                    "Возможные причины: модель не поддерживает изображения, либо проблема с сетью. "
                    "Попробуйте сменить OPENROUTER_MODEL на vision-модель, например: openai/gpt-4o-mini"
                ),
            )
        except httpx.HTTPStatusError as e:
            logger.error("OpenRouter API error: %s", e.response.text)
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"OpenRouter error: {e.response.text[:400]}",
            )
        except httpx.ConnectTimeout:
            logger.error("Timeout connecting to OpenRouter Vision API")
            raise HTTPException(
                status_code=504,
                detail="Превышено время ожидания ответа от Vision API. Попробуйте уменьшить размер изображения.",
            )
        except Exception as e:
            logger.exception("Unexpected error for Vision API: %r", e)
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка Vision API: {type(e).__name__}: {str(e)[:200]}",
            )



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
