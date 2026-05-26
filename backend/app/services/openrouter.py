import base64
import json
import logging

from app.config import settings
from app.services.openrouter_client import chat_completion_with_fallback

from app.schemas import ImageTagSet

logger = logging.getLogger(__name__)

VISION_PROMPT_TEMPLATE = """\
Ты — арт-директор / дизайнер с широкой экспертизой: бренд-идентика, логотипы, \
полиграфия, веб- и мобильный UI, моушн, архитектура и интерьер. Тебе показано \
референсное изображение — это может быть скриншот сайта, фотография объекта, \
логотип, эскиз, упаковка, фотография интерьера, постер, кадр из видео и т.д.

Контекст проекта (если задан — учитывай его при анализе):
- Название проекта: {project_name}
- Описание проекта: {description}

ТВОЯ ЗАДАЧА:
Выделить визуальные характеристики изображения и распределить их по шести категориям \
ниже. Заполняй ТОЛЬКО ТЕ КАТЕГОРИИ, которые ДЕЙСТВИТЕЛЬНО уместны для этого \
изображения и контекста проекта. Если категория не применима (например, в простом \
логотипе нет «UI-элементов», у архитектурного объекта нет «типографики», у фотографии \
интерьера нет «UI-навигации») — оставь массив пустым `[]`. Лучше пустой массив, чем \
выдуманные теги «для галочки».

КАТЕГОРИИ:
1. style — общая стилистика и настроение. Слова сам подбираешь под тип объекта: \
для UI это могут быть "dark mode", "glassmorphism", "brutalism"; для логотипа — \
"монограмма", "геометрический знак", "леттеринг"; для интерьера — "japandi", \
"скандинавский минимализм", "лофт"; для архитектуры — "параметризм", "хай-тек", \
"неоклассика". Не используй абстрактные термины искусствоведения («постмодернизм», \
«эпоха» и т.п.) — только прикладные характеристики.

2. color_palette — фактические цвета объекта в виде HEX-кодов, прочитанных с \
изображения. Можно добавить 1 строку с типом гармонии («монохромная», \
«комплементарная», «аналоговая», «триадная»). Если объект почти бесцветный/ч-б — \
дай 1–2 HEX-а или оставь пустым.

3. typography — заполняй только если на изображении ЕСТЬ значимый текст или \
шрифтовая работа (логотип-леттеринг, заголовки UI, постер, обложка). Опиши тип \
(гротеск/антиква/моноширинный/рукописный), вес, характер, иерархию.

4. composition — общая структура: для UI — сетка и колонки; для логотипа — \
горизонтальная/вертикальная компоновка, симметрия; для интерьера/архитектуры — \
организация пространства, доминанты; для постера — кадрирование и баланс.

5. ui_elements — заполняй ТОЛЬКО если это UI/интерфейс. Для логотипа, фотографии, \
интерьера, упаковки оставь `[]`.

6. visual_hooks — характерные приёмы и детали: свечение, градиенты, текстуры, \
материалы (для архитектуры — бетон/дерево/металл/стекло), свет (для интерьера — \
естественный/тёплый/контрастный), приёмы съёмки и т.п.

ОБЩИЕ ПРАВИЛА:
- Максимум 8 значений в каждой категории, обычно 3–6.
- Будь точным и конкретным. Не повторяй одно и то же разными словами.
- Никаких вводных фраз — только JSON.

ФОРМАТ ОТВЕТА (строго JSON, без markdown-обёртки):
{{
  "style": [...],
  "color_palette": [...],
  "typography": [...],
  "composition": [...],
  "ui_elements": [...],
  "visual_hooks": [...]
}}

Ответ должен начинаться с {{ и заканчиваться на }}.\
"""


async def deconstruct_image_to_tags(
    image_bytes: bytes,
    filename: str = "",
    project_name: str = "",
    description: str = "",
) -> ImageTagSet:
    """Send an image to OpenRouter Vision model and parse structured tags."""
    b64 = base64.b64encode(image_bytes).decode("utf-8")

    # Detect mime type from first bytes
    mime = "image/jpeg"
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        mime = "image/png"
    elif image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        mime = "image/webp"

    prompt = VISION_PROMPT_TEMPLATE.format(
        project_name=(project_name or "не указано").strip() or "не указано",
        description=(description or "не указано").strip() or "не указано",
    )
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
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
