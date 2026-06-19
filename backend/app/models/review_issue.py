from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.app.models.base import Base

class ReviewIssue(Base):
    """
    SQLAlchemy model representing an individual code review issue/finding.
    """
    __tablename__ = "review_issues"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    review_report_id = Column(Integer, ForeignKey("review_reports.id", ondelete="CASCADE"), nullable=False)
    issue_type = Column(String, nullable=False, index=True)  # Security, Logic, Performance, Style
    severity = Column(String, nullable=False, index=True)    # Critical, High, Medium, Low
    line_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    suggested_fix = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    review_report = relationship("ReviewReport", back_populates="issues")
