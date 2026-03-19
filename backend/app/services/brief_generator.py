"""
Brief generation service.

For the ГОСТ 34.602-2020 template the FULL text of the standard PDF is injected
into the AI system prompt so the model follows the REAL document – not a
hand-written interpretation.
"""
import io
import re
import uuid
import json
import logging
import httpx
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from fpdf import FPDF
from pdfminer.high_level import extract_text as pdf_extract_text

from app.schemas import ImageTagSet
from app.config import settings

logger = logging.getLogger(__name__)

GENERATED_DIR = Path("/app/generated")
GENERATED_DIR.mkdir(parents=True, exist_ok=True)

_FONT_DIR = Path(__file__).resolve().parent / "fonts"
_GOST_PDF = Path("/app/app/resources/34.602-2020.pdf")


# ---------------------------------------------------------------------------
# GOST PDF extraction (cached so it only parses the PDF once per process)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _extract_gost_text() -> str:
    """Return the full text of ГОСТ 34.602-2020. Returns '' if PDF not found."""
    if not _GOST_PDF.exists():
        logger.warning("GOST PDF not found at %s", _GOST_PDF)
        return ""
    try:
        text = pdf_extract_text(str(_GOST_PDF))
        # Trim whitespace-only lines and collapse runs of blanks
        lines = [l.rstrip() for l in text.splitlines()]
        text = "\n".join(lines)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        logger.info("GOST PDF loaded: %d chars", len(text))
        return text
    except Exception as exc:
        logger.error("Failed to read GOST PDF: %s", exc)
        return ""


# ---------------------------------------------------------------------------
# PDF rendering helper
# ---------------------------------------------------------------------------

class BriefPDF(FPDF):
    """Custom PDF with Cyrillic support via DejaVu fonts."""

    def __init__(self):
        super().__init__()
        font_path = _FONT_DIR / "DejaVuSans.ttf"
        bold_font_path = _FONT_DIR / "DejaVuSans-Bold.ttf"
        if font_path.exists():
            self.add_font("DejaVu", "", str(font_path), uni=True)
            if bold_font_path.exists():
                self.add_font("DejaVu", "B", str(bold_font_path), uni=True)
            self._font_family = "DejaVu"
        else:
            self._font_family = "Helvetica"

    def header(self):
        self.set_font(self._font_family, "B", 14)
        # "MoodBrief — Техническое задание"
        self.cell(
            0, 10,
            "MoodBrief \u2014 \u0422\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u043e\u0435"
            " \u0437\u0430\u0434\u0430\u043d\u0438\u0435",
            ln=True, align="C",
        )
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font(self._font_family, "", 8)
        self.set_text_color(150, 150, 150)
        # "Стр. X/{nb}"
        self.cell(
            0, 10,
            "\u0421\u0442\u0440. " + str(self.page_no()) + "/{nb}",
            align="C",
        )


# ---------------------------------------------------------------------------
# Tag collection
# ---------------------------------------------------------------------------

def _collect_all_tags(tags: list[ImageTagSet]) -> dict[str, list[str]]:
    merged: dict[str, set[str]] = {
        "style": set(),
        "color_palette": set(),
        "typography": set(),
        "composition": set(),
        "ui_elements": set(),
        "visual_hooks": set(),
    }
    for t in tags:
        merged["style"].update(t.style)
        merged["color_palette"].update(t.color_palette)
        merged["typography"].update(t.typography)
        merged["composition"].update(t.composition)
        merged["ui_elements"].update(t.ui_elements)
        merged["visual_hooks"].update(t.visual_hooks)
    return {k: sorted(v) for k, v in merged.items()}


# ---------------------------------------------------------------------------
# System message (shared for all templates)
# ---------------------------------------------------------------------------

_BASE_SYSTEM = """\
Ты — эксперт по технической и проектной документации с 25-летним опытом.
Ты составлял ТЗ для крупных государственных и коммерческих проектов.

СТРОГИЕ ПРАВИЛА — нарушение любого из них недопустимо:
1. Отвечай ИСКЛЮЧИТЕЛЬНО на русском языке.
   - Запрещено использовать английские слова в русском тексте, \
даже в технических контекстах.
   - Вместо "users" пиши "пользователей"; вместо "uptime" — "доступность"; \
вместо "deployment" — "развёртывание"; вместо "organization" — "организация".
   - Технические названия технологий (React, PostgreSQL, Docker) — допустимы, \
всё остальное — только по-русски.
2. Отвечай ТОЛЬКО в формате Markdown. Никаких вводных ("Конечно!") \
или заключительных ("Надеюсь, это поможет!") фраз.
3. КАЖДЫЙ раздел ОБЯЗАН содержать реальный развёрнутый текст. \
ЗАПРЕЩЕНО оставлять разделы пустыми или писать-заглушки вроде \
"[заполнить]", "[уточнить]", "[вставить]".
4. Если данных мало — додумывай профессионально, опираясь на описание проекта.
5. Используй таблицы для структурированных данных (функции, этапы, документы).
6. Не повторяй одинаковые абзацы или заголовки.\
"""


# ---------------------------------------------------------------------------
# GOST template — uses the real PDF text as authoritative reference
# ---------------------------------------------------------------------------

_GOST_STRUCTURE_INSTRUCTIONS = """\
Создай Техническое Задание СТРОГО по ГОСТ 34.602-2020.

КРИТИЧЕСКИ ВАЖНО:
- Структура документа должна ТОЧНО СООТВЕТСТВОВАТЬ разделам ГОСТ 34.602-2020, \
приведённым ниже в тексте стандарта.
- Каждый раздел и подраздел заполни РЕАЛЬНЫМ содержательным текстом. \
Не оставляй ни одной пустой строки там, где ожидается текст.
- Все перечисления оформляй в виде таблиц Markdown.
- Разделы с этапами и сроками: все ячейки таблицы должны содержать \
конкретный текст, реалистичные даты начиная с {today}.

ОБЯЗАТЕЛЬНАЯ СТРУКТУРА (строго по ГОСТу):

# Техническое задание на создание автоматизированной системы «[наименование]»
_ГОСТ 34.602-2020_

---

## 1. Общие сведения

### 1.1 Полное наименование системы
Напиши полное официальное наименование и аббревиатуру АС.

### 1.2 Шифр темы или договора
Укажи шифр, например: МБ-2026/01.

### 1.3 Организации-участники

| Роль | Наименование | Адрес / контакт |
|------|-------------|----------------|
| Заказчик | [Организация-заказчик] | [реквизиты] |
| Разработчик | [Организация-разработчик] | [реквизиты] |

### 1.4 Плановые сроки выполнения работ

| № | Стадия | Дата начала | Дата окончания |
|---|--------|-------------|----------------|
| 1 | Формирование требований | {today} | [дата] |
| 2 | Разработка концепции | [дата] | [дата] |
| 3 | Разработка ТЗ | [дата] | [дата] |
| 4 | Эскизный проект | [дата] | [дата] |
| 5 | Технический проект | [дата] | [дата] |
| 6 | Рабочая документация | [дата] | [дата] |
| 7 | Ввод в действие | [дата] | [дата] |

ОБЯЗАТЕЛЬНО: замени все [дата] на реалистичные конкретные даты (формат ДД.ММ.ГГГГ).

### 1.5 Источник финансирования
Укажи конкретный источник.

### 1.6 Порядок оформления и предъявления результатов
Опиши процедуру сдачи: состав пакета документов, подписание актов, приёмочная комиссия.

---

## 2. Назначение и цели создания системы

### 2.1 Назначение системы
Напиши 2–3 абзаца: вид деятельности, объекты автоматизации, пользователи.

### 2.2 Цели создания системы

| № | Цель | Ожидаемый результат | Показатель (KPI) |
|---|------|--------------------|--------------------|

Заполни минимум 5 строк с конкретными измеримыми целями.

---

## 3. Характеристика объектов автоматизации

### 3.1 Краткие сведения об объекте автоматизации
2–3 абзаца о текущем состоянии и основных процессах объекта.

### 3.2 Условия эксплуатации
Режим работы, ожидаемая нагрузка (в единицах: запросов в секунду, \
обращений в сутки — НЕ "users"), требования к инфраструктуре.

### 3.3 Ключевые автоматизируемые процессы
Перечисли как минимум 5 конкретных процессов с описанием.

---

## 4. Требования к системе

### 4.1 Требования к системе в целом

#### 4.1.1 Требования к структуре и функционированию
Архитектура (тип: клиент-серверная / микросервисная / SaaS), \
основные подсистемы, взаимодействие компонентов.

#### 4.1.2 Требования к численности и квалификации персонала

| Роль | Кол-во | Требуемая квалификация | Функции |
|------|--------|------------------------|---------|

#### 4.1.3 Показатели надёжности и доступности
Конкретные числа: доступность (%), среднее время между отказами (ч), \
время восстановления (мин), пиковая нагрузка (запросов/сек).

#### 4.1.4 Требования к надёжности и резервированию
Резервирование серверов, частота резервного копирования, \
план восстановления (RTO и RPO в часах).

#### 4.1.5 Требования к информационной безопасности
Аутентификация (тип), авторизация (модель), шифрование, \
защита от несанкционированного доступа, журналирование событий.

### 4.2 Требования к функциям (задачам) системы

| Подсистема | Функция | Приоритет | Описание |
|------------|---------|-----------|----------|

Заполни минимум 12 строк, сгруппировав по подсистемам.

### 4.3 Требования к видам обеспечения

#### 4.3.1 Математическое обеспечение
Алгоритмы и методы обработки данных (поиск, фильтрация, аналитика и т.д.).

#### 4.3.2 Информационное обеспечение
СУБД, схема данных, форматы обмена (JSON/XML), справочники.

#### 4.3.3 Программное обеспечение

| Компонент | Технология | Версия | Назначение |
|-----------|-----------|--------|------------|

Конкретный современный стек для 2026 года.

#### 4.3.4 Техническое обеспечение
Серверная конфигурация (процессор / оперативная память / диск), \
требования к клиентским устройствам.

#### 4.3.5 Организационное обеспечение
Структура службы эксплуатации: роли, регламенты, режим сопровождения.

---

## 5. Состав и содержание работ по созданию системы

| № | Стадия / Этап | Содержание работ | Исполнитель | Срок |
|---|--------------|-----------------|-------------|------|

Заполни ВСЕ 7 строк (стадии из ГОСТ 34.602-2020): \
конкретные работы, исполнитель, реалистичные сроки.

---

## 6. Порядок контроля и приёмки системы

### 6.1 Виды и методы испытаний
Предварительные испытания (у разработчика), опытная эксплуатация (у заказчика), \
приёмочные испытания (комиссия). Для каждого: цель, методы, критерии.

### 6.2 Состав приёмочной комиссии

| Роль в комиссии | Должность | Организация |
|----------------|-----------|-------------|

### 6.3 Критерии успешной приёмки
Перечисли 6–8 конкретных измеримых критериев готовности системы.

---

## 7. Требования к подготовке объекта автоматизации к вводу системы в действие
Обучение персонала (план, сроки), миграция данных (источники, формат, объём), \
адаптация бизнес-процессов, формирование инфраструктуры.

---

## 8. Требования к документированию

| № | Наименование документа | На основании |
|---|------------------------|-------------|

Перечисли минимум 8 документов (ТЗ, Пояснительная записка, \
Руководство пользователя, Руководство администратора, \
Программа и методика испытаний, Описание БД и пр.).

---

## 9. Источники разработки

- ГОСТ 34.602-2020 «Техническое задание на создание автоматизированной системы»
- Техническое задание заказчика (первичные требования)
- Результаты анализа референсных изображений проекта
- Материалы интервью с заказчиком
"""


_TEMPLATE_STANDARD = """\
Создай профессиональное Техническое Задание (ТЗ) для цифрового продукта.

ОБЯЗАТЕЛЬНАЯ СТРУКТУРА — каждый раздел заполни реальным экспертным содержанием:

# [Название проекта] — Техническое задание

## 1. Общие сведения и цели проекта
Напиши 3–4 абзаца: наименование, назначение, бизнес-цели, ожидаемый результат, \
заказчик и исполнитель.

## 2. Целевая аудитория
Создай 3 детальных портрета пользователей. Для каждой персоны: \
имя и возраст (условный), профессия и технический уровень, задача, сценарий использования.

## 3. Функциональные требования

| № | Функция | Приоритет | Описание |
|---|---------|-----------|----------|

Минимум 12 функций. Приоритет: П1 — критично, П2 — важно, П3 — желательно.

## 4. Дизайн и визуальная концепция
На основе visual_tags:
- **Стилистика:** общий визуальный стиль
- **Цветовая палитра:** цвета с их ролью и hex-кодами
- **Типографика:** шрифты, иерархия заголовков
- **Компоновка:** сетка, отступы, принципы компоновки
- **Компоненты интерфейса:** кнопки, карточки, формы

## 5. Технические требования

### 5.1 Стек технологий
Конкретный стек на 2026 год (интерфейс / сервер / база данных / хостинг / CI/CD).

### 5.2 Производительность
- Время первой загрузки (LCP) — не более секунд
- Доступность — не менее %
- Пиковая нагрузка — не менее одновременных сеансов
- Основные показатели качества веб-страниц (Core Web Vitals)

### 5.3 Безопасность
Аутентификация, авторизация, шифрование, защита от уязвимостей (OWASP).

### 5.4 Совместимость
Браузеры, операционные системы, разрешения экрана, мобильные устройства.

## 6. Этапы и сроки разработки

| № | Этап | Содержание работ | Срок |
|---|------|-----------------|------|

Минимум 5 реалистичных этапов со сроками в неделях.

## 7. Критерии приёмки
Не менее 8 конкретных измеримых критериев готовности.

## 8. Риски и план митигации

| Риск | Вероятность | Влияние | Меры снижения |
|------|------------|---------|--------------|

4–5 типичных рисков с планом снижения.
"""


_TEMPLATE_CREATIVE = """\
Создай вдохновляющий Креативный бриф для дизайн-команды.

Пиши только на русском языке. Используй visual_tags как основной источник.

---

# [Название проекта] — Креативный бриф

## 1. Суть проекта и ДНК бренда
3–4 абзаца: core-идея, место на рынке, ценностное предложение. \
5 прилагательных-характеристик бренда. Ключевой слоган.

## 2. Эмоциональный ландшафт
Эмоция при первом взгляде, яркая метафора продукта. \
5–7 ключевых ощущений с объяснением откуда они берутся в дизайне.

## 3. Визуальный язык — Цвет

| Цвет | Hex | Роль | Эмоциональный смысл |
|------|-----|------|---------------------|

На основе color_palette тегов.

## 4. Визуальный язык — Типографика
Основной и дополнительный шрифты, иерархия H1/H2/H3/body/caption, \
правила применения (из тегов typography).

## 5. Визуальный язык — Компоненты и компоновка
Стиль кнопок, карточек, форм; сетка (колонки, отступы, брейкпоинты); \
принципы whitespace; тип анимаций и переходов.

## 6. Visual Hooks — Уникальные фишки
6–8 конкретных визуальных приёмов (из тегов visual_hooks): \
название + где применяется + почему запоминается.

## 7. Референсы настроения
4–6 конкретных референсов (бренды, архитекторы, эпохи): \
что именно взять + чего избегать в каждом.

## 8. Голос бренда
Формальность, юмор, краткость. \
3 примера: как НЕ говорит бренд vs как говорит.

## 9. Что делать и чего избегать

| ✅ Делать | ❌ Не делать |
|----------|------------|

Минимум 7 пунктов в каждой колонке.
"""


# ---------------------------------------------------------------------------
# Main generation function
# ---------------------------------------------------------------------------

async def generate_brief_via_ai(
    tags: list[ImageTagSet],
    project_name: str,
    description: str = "",
    selected_fonts: list[str] | None = None,
    selected_colors: list[str] | None = None,
    template_id: str = "standard",
    user_notes: str = "",
) -> str:
    """Compose a Markdown brief from AI tags + user inputs using LLM."""
    merged = _collect_all_tags(tags)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    today_ru = datetime.now(timezone.utc).strftime("%d.%m.%Y")

    context_str = json.dumps(
        {
            "project_name": project_name,
            "description": description,
            "selected_fonts": selected_fonts or [],
            "selected_colors": selected_colors or [],
            "user_notes": user_notes,
            "visual_tags": merged,
        },
        ensure_ascii=False,
        indent=2,
    )

    # Build system message — inject GOST PDF for gost template
    system_message = _BASE_SYSTEM
    if (template_id or "standard") == "gost":
        gost_text = _extract_gost_text()
        if gost_text:
            system_message = (
                _BASE_SYSTEM
                + "\n\n"
                + "=" * 60
                + "\n"
                + "ПОЛНЫЙ ТЕКСТ ГОСТ 34.602-2020 (авторитетный источник структуры):\n"
                + "=" * 60
                + "\n"
                + gost_text[:12000]  # trim to avoid context overflow
            )
            logger.info("Injected GOST PDF text (%d chars) into system prompt", len(gost_text))

    # Select template
    if (template_id or "standard") == "gost":
        user_prompt_template = _GOST_STRUCTURE_INSTRUCTIONS.format(today=today_ru)
    elif (template_id or "standard") == "creative":
        user_prompt_template = _TEMPLATE_CREATIVE
    else:
        user_prompt_template = _TEMPLATE_STANDARD

    user_message = (
        f"{user_prompt_template}\n\n"
        "---\n"
        f"ДАННЫЕ О ПРОЕКТЕ (используй для наполнения всех разделов):\n\n"
        f"{context_str}\n\n"
        f"_Дата составления ТЗ: {today_ru}_"
    )

    payload = {
        "model": settings.OPENROUTER_TEXT_MODEL,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
        "max_tokens": 6000,
        "temperature": 0.2,
    }

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://moodbrief.app",
        "X-Title": "MoodBrief",
    }

    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(
            f"{settings.OPENROUTER_BASE_URL}/chat/completions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

    raw_text = data["choices"][0]["message"]["content"].strip()

    # Strip markdown code fences if model wrapped the output
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        if len(lines) > 1:
            raw_text = "\n".join(lines[1:])
        if raw_text.endswith("```"):
            raw_text = raw_text[: -len("```")]

    return raw_text.strip()


# ---------------------------------------------------------------------------
# AI refinement of existing brief
# ---------------------------------------------------------------------------

async def refine_brief_via_ai(current_markdown: str, instruction: str) -> str:
    """Apply a user instruction to an existing brief and return updated Markdown."""
    system_message = (
        _BASE_SYSTEM
        + "\n\nТвоя задача: отредактировать готовое ТЗ согласно инструкции пользователя. "
        "Верни ПОЛНЫЙ обновлённый документ в формате Markdown. "
        "Не добавляй вводных фраз. Сохрани общую структуру, если инструкция не требует иного."
    )
    user_message = (
        f"ИНСТРУКЦИЯ ПО РЕДАКТИРОВАНИЮ:\n{instruction}\n\n"
        f"---\nТЕКУЩЕЕ ТЗ:\n\n{current_markdown}"
    )

    payload = {
        "model": settings.OPENROUTER_TEXT_MODEL,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
        "max_tokens": 6000,
        "temperature": 0.2,
    }
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://moodbrief.app",
        "X-Title": "MoodBrief",
    }

    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(
            f"{settings.OPENROUTER_BASE_URL}/chat/completions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

    raw = data["choices"][0]["message"]["content"].strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        if len(lines) > 1:
            raw = "\n".join(lines[1:])
        if raw.endswith("```"):
            raw = raw[: -len("```")]
    return raw.strip()


# ---------------------------------------------------------------------------
# PDF generation
# ---------------------------------------------------------------------------

def generate_brief_pdf(markdown_text: str, project_name: str = "brief") -> str:
    """Convert brief markdown to PDF, return filename."""
    pdf = BriefPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    font = pdf._font_family

    content_lines = markdown_text.split("\n")
    i = 0
    while i < len(content_lines):
        line = content_lines[i]
        stripped = line.strip()

        if pdf.get_x() > pdf.l_margin:
            pdf.ln()

        if stripped.startswith("#### "):
            pdf.set_font(font, "B", 10)
            pdf.ln(1)
            pdf.multi_cell(0, 5, stripped[5:])
            pdf.ln(1)

        elif stripped.startswith("### "):
            pdf.set_font(font, "B", 11)
            pdf.ln(1)
            pdf.multi_cell(0, 6, stripped[4:])
            pdf.ln(1)

        elif stripped.startswith("## "):
            pdf.set_font(font, "B", 13)
            pdf.ln(2)
            pdf.multi_cell(0, 7, stripped[3:])
            pdf.ln(2)

        elif stripped.startswith("# "):
            pdf.set_font(font, "B", 16)
            pdf.multi_cell(0, 8, stripped[2:])
            pdf.ln(3)

        elif stripped.startswith("---"):
            pdf.ln(3)
            pdf.set_draw_color(200, 200, 200)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(3)

        elif stripped.startswith("|"):
            # Skip separator rows
            if all(c in "| -:" for c in stripped):
                i += 1
                continue
            # Collect all table rows
            table_data: list[list[str]] = []
            while i < len(content_lines) and content_lines[i].strip().startswith("|"):
                row_stripped = content_lines[i].strip()
                if not all(c in "| -:" for c in row_stripped):
                    cells = [c.strip() for c in row_stripped.split("|")[1:-1]]
                    if cells:
                        table_data.append(cells)
                i += 1
            if table_data:
                pdf.set_font(font, "", 9)
                with pdf.table(
                    borders_layout="SINGLE_TOP_LINE",
                    cell_fill_color=245,
                    cell_fill_mode="ROWS",
                    line_height=5,
                    text_align="LEFT",
                    width=190,
                ) as table:
                    for row_cells in table_data:
                        row = table.row()
                        for cell_text in row_cells:
                            row.cell(re.sub(r"[`*_]", "", cell_text))
                pdf.ln(2)
            continue  # i was already advanced by inner loop

        elif stripped.startswith("- ") or stripped.startswith("* "):
            pdf.set_font(font, "", 10)
            clean = re.sub(r"[`*_]", "", stripped[2:])
            pdf.cell(5, 6, "  \u2013")
            pdf.multi_cell(185, 6, clean)
            if pdf.get_x() > pdf.l_margin:
                pdf.ln(1)

        elif stripped.startswith("_") and stripped.endswith("_") and len(stripped) > 2:
            pdf.set_font(font, "", 9)
            pdf.set_text_color(120, 120, 120)
            pdf.multi_cell(0, 5, stripped.strip("_"))
            pdf.set_text_color(0, 0, 0)
            pdf.ln(1)

        elif not stripped:
            pdf.ln(3)

        else:
            # Numbered section heading detection: "1.", "1.1", "4.1.2" etc.
            is_numbered = bool(re.match(r"^\d+(\.\d+)*\.?\s+\S", stripped))
            clean = re.sub(r"\*\*(.+?)\*\*", r"\1", stripped)
            clean = re.sub(r"[`_]", "", clean)
            if is_numbered:
                pdf.set_font(font, "B", 11)
                pdf.ln(1)
                pdf.multi_cell(0, 6, clean)
                pdf.ln(1)
            else:
                pdf.set_font(font, "", 10)
                pdf.multi_cell(0, 6, clean)

        i += 1

    slug = re.sub(r"[^a-zA-Z0-9]", "_", project_name)[:40]
    filename = f"{slug}_{uuid.uuid4().hex[:8]}.pdf"
    pdf.output(str(GENERATED_DIR / filename))
    return filename
