from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Image analysis ────────────────────────────────────────────────────────────


class ImageTagSet(BaseModel):
    """Structured tags extracted from a single image by the Vision model."""

    style: list[str] = Field(default_factory=list, description="Название стиля, эпоха, настроение")
    color_palette: list[str] = Field(default_factory=list, description="Hex-коды, соотношение цветов, тип гармонии")
    typography: list[str] = Field(default_factory=list, description="Тип шрифта: гротеск/антиква, начертание, иерархия")
    composition: list[str] = Field(default_factory=list, description="Сетка, баланс, фокусные точки, использование негативного пространства")
    ui_elements: list[str] = Field(default_factory=list, description="Формы кнопок, скругления, стиль иконок, тени/градиенты")
    visual_hooks: list[str] = Field(default_factory=list, description="Необычные графические приемы, текстуры, эффекты")
    filename: str = ""


class AnalyzeImagesResponse(BaseModel):
    project_id: uuid.UUID
    tags: list[ImageTagSet]


# ── Brief generation ─────────────────────────────────────────────────────────


class GenerateBriefRequest(BaseModel):
    project_id: uuid.UUID
    confirmed_tags: list[ImageTagSet] = Field(default_factory=list)
    user_notes: str = ""
    selected_fonts: list[str] = Field(default_factory=list)
    selected_colors: list[str] = Field(default_factory=list)
    template_id: str = "standard"


class GenerateBriefResponse(BaseModel):
    project_id: uuid.UUID
    brief_markdown: str
    pdf_url: str


# ── Project / history ─────────────────────────────────────────────────────────


class ProjectOut(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = ""
    selected_fonts: list = Field(default_factory=list)
    selected_colors: list = Field(default_factory=list)
    image_tags: list = Field(default_factory=list)
    brief_markdown: Optional[str] = ""
    pdf_filename: Optional[str] = ""
    status: str = "draft"
    template_id: Optional[str] = "standard"
    created_at: datetime

    class Config:
        from_attributes = True
