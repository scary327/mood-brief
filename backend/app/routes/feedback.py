import logging
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Feedback, Project

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["feedback"])

# Spam detection: block obviously bad comments
_SPAM_PATTERNS = [
    re.compile(r"(.)\1{6,}"),          # 7+ repeated chars (e.g. "ааааааааа")
    re.compile(r"(..+)\1{3,}"),         # Repeating phrase
    re.compile(r"http[s]?://"),          # URLs
    re.compile(r"[A-Z]{10,}"),           # ALL CAPS spam
]

_BAD_WORDS_SAMPLE = {"shit", "fuck", "pussy", "ass" , "dick"}  # extend as needed


def _is_spam(comment: str) -> bool:
    """Return True if the comment looks like spam or is abusive."""
    if not comment or len(comment.strip()) < 3:
        return False
    text = comment.lower().strip()
    for pat in _SPAM_PATTERNS:
        if pat.search(text):
            logger.info("Spam pattern detected in feedback comment")
            return True
    words = set(re.findall(r"\w+", text))
    if words & _BAD_WORDS_SAMPLE:
        logger.info("Bad words detected in feedback comment")
        return True
    # Very long repeated nonsense
    if len(comment) > 2000:
        return True
    return False


class FeedbackCreate(BaseModel):
    project_id: str
    rating: int   # 1-5
    comment: str = ""


class FeedbackResponse(BaseModel):
    id: str
    message: str


@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(body: FeedbackCreate, db: Session = Depends(get_db)):
    """Submit user feedback (rating + comment) for a generated brief."""
    if body.rating < 1 or body.rating > 5:
        raise HTTPException(status_code=422, detail="Rating must be between 1 and 5")

    project = db.query(Project).filter(Project.id == body.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Moderation: save but mark as not published if spammy
    is_published = not _is_spam(body.comment)

    fb = Feedback(
        project_id=project.id,
        rating=body.rating,
        comment=body.comment.strip()[:2000],
        is_published=is_published,
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)

    # Always tell the user we received their feedback (don't reveal moderation)
    return FeedbackResponse(
        id=str(fb.id),
        message="Мы учтём ваши пожелания. Спасибо за обратную связь!",
    )


@router.get("/feedback/{project_id}")
def get_feedback_for_project(project_id: str, db: Session = Depends(get_db)):
    """Get published feedback for a project."""
    items = (
        db.query(Feedback)
        .filter(Feedback.project_id == project_id, Feedback.is_published == True)
        .order_by(Feedback.created_at.desc())
        .all()
    )
    return [
        {
            "id": str(f.id),
            "rating": f.rating,
            "comment": f.comment,
            "created_at": f.created_at.isoformat(),
        }
        for f in items
    ]
