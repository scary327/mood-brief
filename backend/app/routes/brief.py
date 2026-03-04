import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project
from app.schemas import GenerateBriefRequest, GenerateBriefResponse, ImageTagSet
from app.services.brief_generator import (
    GENERATED_DIR,
    generate_brief_via_ai,
    generate_brief_pdf,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["brief"])


@router.post("/generate-brief", response_model=GenerateBriefResponse)
async def generate_brief(body: GenerateBriefRequest, db: Session = Depends(get_db)):
    """Generate Markdown + PDF brief from confirmed tags."""
    project = db.query(Project).filter(Project.id == body.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Use confirmed tags if provided, else fall back to stored ones
    if body.confirmed_tags:
        tags = body.confirmed_tags
    else:
        tags = [ImageTagSet(**t) for t in (project.image_tags or [])]

    markdown = await generate_brief_via_ai(
        tags=tags,
        project_name=project.name,
        description=project.description or "",
        selected_fonts=body.selected_fonts or project.selected_fonts,
        selected_colors=body.selected_colors or project.selected_colors,
        user_notes=body.user_notes,
    )

    pdf_filename = generate_brief_pdf(markdown, project_name=project.name)

    project.brief_markdown = markdown
    project.pdf_filename = pdf_filename
    project.status = "ready"
    db.commit()

    return GenerateBriefResponse(
        project_id=project.id,
        brief_markdown=markdown,
        pdf_url=f"/api/brief/{project.id}/pdf",
    )


@router.get("/brief/{project_id}/pdf")
def download_pdf(project_id: str, db: Session = Depends(get_db)):
    """Download the generated PDF for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or not project.pdf_filename:
        raise HTTPException(status_code=404, detail="PDF not found")

    filepath = GENERATED_DIR / project.pdf_filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="PDF file missing from disk")

    return FileResponse(
        path=str(filepath),
        media_type="application/pdf",
        filename=project.pdf_filename,
    )
