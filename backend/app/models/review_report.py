from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.app.models.base import Base

class ReviewReport(Base):
    """
    SQLAlchemy model representing a code review session report for a file in a PR.
    """
    __tablename__ = "review_reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pull_request_id = Column(Integer, ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String, nullable=False, index=True)
    reviewed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    pull_request = relationship("PullRequest", back_populates="review_reports")
    issues = relationship(
        "ReviewIssue",
        back_populates="review_report",
        cascade="all, delete-orphan"
    )
