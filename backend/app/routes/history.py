from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project
from app.schemas import ProjectOut

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/history", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    """Return all projects, newest first."""
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    return projects


@router.get("/history/{project_id}", response_model=ProjectOut)
def get_project(project_id: str, db: Session = Depends(get_db)):
    """Return a single project by ID."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
