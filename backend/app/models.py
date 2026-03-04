import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True, default="")
    selected_fonts = Column(JSON, nullable=True, default=list)
    selected_colors = Column(JSON, nullable=True, default=list)
    image_tags = Column(JSON, nullable=True, default=list)
    brief_markdown = Column(Text, nullable=True, default="")
    pdf_filename = Column(String(255), nullable=True, default="")
    status = Column(String(50), nullable=False, default="draft")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
