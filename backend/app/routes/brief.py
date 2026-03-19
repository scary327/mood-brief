import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project
from app.schemas import GenerateBriefRequest, GenerateBriefResponse, ImageTagSet
from app.services.brief_generator import (
    GENERATED_DIR,
    generate_brief_via_ai,
    generate_brief_pdf,
    refine_brief_via_ai,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["brief"])


@router.post("/generate-brief", response_model=GenerateBriefResponse)
async def generate_brief(body: GenerateBriefRequest, db: Session = Depends(get_db)):
    """Generate Markdown + PDF brief from confirmed tags."""
    project = db.query(Project).filter(Project.id == body.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.template_id = body.template_id
    project.selected_fonts = body.selected_fonts
    project.selected_colors = body.selected_colors
    project.image_tags = [t.model_dump() for t in body.confirmed_tags]

    if body.user_notes:
        project.description = body.user_notes

    db.commit()

    markdown = await generate_brief_via_ai(
        tags=body.confirmed_tags,
        project_name=project.name,
        description=project.description or "",
        selected_fonts=body.selected_fonts,
        selected_colors=body.selected_colors,
        template_id=body.template_id,
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


# ── Save edited markdown ───────────────────────────────────────────────────

class SaveMarkdownRequest(BaseModel):
    markdown: str


@router.put("/projects/{project_id}/markdown")
def save_markdown(
    project_id: str,
    body: SaveMarkdownRequest,
    db: Session = Depends(get_db),
):
    """Save manually-edited markdown and regenerate the PDF."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    pdf_filename = generate_brief_pdf(body.markdown, project_name=project.name)
    project.brief_markdown = body.markdown
    project.pdf_filename = pdf_filename
    db.commit()

    return {"ok": True, "pdf_url": f"/api/brief/{project_id}/pdf"}


# ── AI refinement of existing brief ──────────────────────────────────────

class RefineBriefRequest(BaseModel):
    project_id: str
    instruction: str


class RefineBriefResponse(BaseModel):
    brief_markdown: str
    pdf_url: str


@router.post("/refine-brief", response_model=RefineBriefResponse)
async def refine_brief(body: RefineBriefRequest, db: Session = Depends(get_db)):
    """Apply a user instruction to the existing brief via AI, save and return."""
    project = db.query(Project).filter(Project.id == body.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.brief_markdown:
        raise HTTPException(status_code=400, detail="No brief to refine")
    if not body.instruction.strip():
        raise HTTPException(status_code=422, detail="Instruction cannot be empty")

    updated_markdown = await refine_brief_via_ai(
        current_markdown=project.brief_markdown,
        instruction=body.instruction,
    )

    pdf_filename = generate_brief_pdf(updated_markdown, project_name=project.name)
    project.brief_markdown = updated_markdown
    project.pdf_filename = pdf_filename
    db.commit()

    return RefineBriefResponse(
        brief_markdown=updated_markdown,
        pdf_url=f"/api/brief/{body.project_id}/pdf",
    )
