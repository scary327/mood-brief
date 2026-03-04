import os
import re
import uuid
import json
import httpx
from datetime import datetime, timezone
from pathlib import Path

from fpdf import FPDF

from app.schemas import ImageTagSet
from app.config import settings

from app.schemas import ImageTagSet

GENERATED_DIR = Path("/app/generated")
GENERATED_DIR.mkdir(parents=True, exist_ok=True)

# Path to a bundled font that supports Cyrillic (DejaVu Sans)
_FONT_DIR = Path(__file__).resolve().parent / "fonts"


class BriefPDF(FPDF):
    """Custom PDF with Cyrillic support."""

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
        self.cell(0, 10, "MoodBrief — Техническое задание", ln=True, align="C")
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font(self._font_family, "", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Стр. {self.page_no()}/{{nb}}", align="C")


def _collect_all_tags(tags: list[ImageTagSet]) -> dict[str, list[str]]:
    """Merge tags from all images, deduplicate."""
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


async def generate_brief_via_ai(
    tags: list[ImageTagSet],
    project_name: str,
    description: str = "",
    selected_fonts: list[str] | None = None,
    selected_colors: list[str] | None = None,
    user_notes: str = "",
) -> str:
    """Compose a Markdown brief from AI tags + user inputs using LLM."""
    merged = _collect_all_tags(tags)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    
    context_str = json.dumps({
        "project_name": project_name,
        "description": description,
        "selected_fonts": selected_fonts or [],
        "selected_colors": selected_colors or [],
        "user_notes": user_notes,
        "accumulated_tags": merged
    }, ensure_ascii=False, indent=2)

    prompt = f"""Вот наборы тегов от {len(tags)} референсов и параметры проекта. Синтезируй их в единый гайдлайн для дизайнера (Техническое задание). 
Убери противоречия (если на одной картинке был минимализм, а на другой барокко — выдели это как выбор стиля или найди компромисс).

Данные проекта:
{context_str}

Требования к формату ответа:
- Отвечай ТОЛЬКО в формате Markdown. Никакого вводного текста.
- Не используй блоки кода (```markdown ... ```), просто пиши чистый Markdown текст.
- Создай красивую структуру: заголовки (#, ##, ###), списки, таблицы (особенно для цветовой палитры).
- Обязательно добавь заголовок 1 уровня с названием проекта.
- В конце напиши строку: _Сгенерировано MoodBrief • {now}_
"""

    payload = {
        "model": settings.OPENROUTER_TEXT_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 3000,
        "temperature": 0.4,
    }

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://moodbrief.app",
        "X-Title": "MoodBrief",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{settings.OPENROUTER_BASE_URL}/chat/completions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

    raw_text = data["choices"][0]["message"]["content"].strip()

    if raw_text.startswith("```"):
        lines = raw_text.split("\\n")
        if len(lines) > 1:
            raw_text = "\\n".join(lines[1:])
        if raw_text.endswith("```"):
            raw_text = raw_text[: -len("```")]

    return raw_text.strip()


def generate_brief_pdf(markdown_text: str, project_name: str = "brief") -> str:
    """Convert brief markdown to PDF, return filename."""
    pdf = BriefPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    font = pdf._font_family

    for line in markdown_text.split("\n"):
        stripped = line.strip()

        # Heading 1
        if stripped.startswith("# "):
            pdf.set_font(font, "B", 16)
            pdf.multi_cell(0, 8, stripped[2:])
            pdf.ln(3)

        # Heading 2
        elif stripped.startswith("## "):
            pdf.set_font(font, "B", 13)
            pdf.ln(2)
            pdf.multi_cell(0, 7, stripped[3:])
            pdf.ln(2)

        # Heading 3
        elif stripped.startswith("### "):
            pdf.set_font(font, "B", 11)
            pdf.ln(1)
            pdf.multi_cell(0, 6, stripped[4:])
            pdf.ln(1)

        # Horizontal rule
        elif stripped.startswith("---"):
            pdf.ln(3)
            pdf.set_draw_color(200, 200, 200)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(3)

        # Table rows (simple)
        elif stripped.startswith("|") and "---" not in stripped:
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            pdf.set_font(font, "", 10)
            for cell in cells:
                clean = re.sub(r"[`*_]", "", cell)
                pdf.cell(90, 6, clean, border=0)
            pdf.ln()

        # List items
        elif stripped.startswith("- "):
            pdf.set_font(font, "", 10)
            clean = re.sub(r"[`*_]", "", stripped[2:])
            pdf.cell(6, 6, chr(8226))
            pdf.multi_cell(0, 6, f" {clean}")

        # Italic metadata
        elif stripped.startswith("_") and stripped.endswith("_"):
            pdf.set_font(font, "", 9)
            pdf.set_text_color(120, 120, 120)
            pdf.multi_cell(0, 5, stripped.strip("_"))
            pdf.set_text_color(0, 0, 0)
            pdf.ln(1)

        # Empty line
        elif not stripped:
            pdf.ln(3)

        # Regular text
        else:
            pdf.set_font(font, "", 10)
            pdf.multi_cell(0, 6, stripped)

    slug = re.sub(r"[^a-zA-Zа-яА-Я0-9]", "_", project_name)[:40]
    filename = f"{slug}_{uuid.uuid4().hex[:8]}.pdf"
    filepath = GENERATED_DIR / filename
    pdf.output(str(filepath))
    return filename
