import base64
import json
import logging

from app.config import settings
from app.services.openrouter_client import chat_completion_with_fallback

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

    data, used_model = await chat_completion_with_fallback(
        payload=payload,
        models=settings.vision_model_chain(),
        timeout=120.0,
    )
    logger.info("Vision tags produced by %s for %s", used_model, filename or "<unnamed>")

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
