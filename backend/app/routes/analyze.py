import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project
from app.schemas import AnalyzeImagesResponse, ImageTagSet
from app.services.openrouter import deconstruct_image_to_tags

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["analyze"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB per file
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


@router.post("/analyze-images", response_model=AnalyzeImagesResponse)
async def analyze_images(
    files: list[UploadFile] = File(...),
    project_name: str = Form("Untitled Project"),
    description: str = Form(""),
    selected_fonts: str = Form("[]"),  # JSON-encoded array
    selected_colors: str = Form("[]"),
    db: Session = Depends(get_db),
):
    """Upload images → run AI Vision analysis → return structured tags."""
    import json as _json

    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    # Validate files
    for f in files:
        if f.content_type not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {f.content_type}. Allowed: {ALLOWED_TYPES}",
            )

    # Create project
    try:
        fonts_list = _json.loads(selected_fonts)
    except _json.JSONDecodeError:
        fonts_list = []

    try:
        colors_list = _json.loads(selected_colors)
    except _json.JSONDecodeError:
        colors_list = []

    project = Project(
        name=project_name,
        description=description,
        selected_fonts=fonts_list,
        selected_colors=colors_list,
        status="analyzing",
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Analyze images concurrently
    async def _analyze_one(upload: UploadFile) -> ImageTagSet:
        content = await upload.read()
        if len(content) > MAX_FILE_SIZE:
            logger.warning("File %s exceeds max size, skipping", upload.filename)
            return ImageTagSet(filename=upload.filename or "")
        return await deconstruct_image_to_tags(content, filename=upload.filename or "")

    tags = await asyncio.gather(*[_analyze_one(f) for f in files])
    tags_list = list(tags)

    # Persist tags
    project.image_tags = [t.model_dump() for t in tags_list]
    project.status = "analyzed"
    db.commit()

    return AnalyzeImagesResponse(project_id=project.id, tags=tags_list)
