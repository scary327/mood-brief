from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, User
from app.schemas import ProjectOut
from app.security import get_current_user

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
def list_projects(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Return all projects owned by the current user."""
    try:
        projects = (
            db.query(Project)
            .filter(Project.user_id == current_user.id)
            .order_by(Project.created_at.desc())
            .all()
        )
        return projects
    except Exception as e:
        import logging
        logging.error(f"Error in list_projects: {str(e)}", exc_info=True)
        raise


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return a single project by ID if it belongs to current user."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check ownership
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this project",
        )
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a single project by ID if it belongs to current user."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check ownership
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this project",
        )
    
    db.delete(project)
    db.commit()


@router.delete("", status_code=204)
def delete_all_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete all projects for current user (clear history)."""
    db.query(Project).filter(Project.user_id == current_user.id).delete()
    db.commit()
