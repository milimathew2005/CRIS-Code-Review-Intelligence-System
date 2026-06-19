from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.app.models.base import Base

class PullRequest(Base):
    """
    SQLAlchemy model representing a pull request inside a repository.
    """
    __tablename__ = "pull_requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    pr_number = Column(Integer, nullable=False, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    action = Column(String, nullable=False)
    github_url = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    repository = relationship("Repository", back_populates="pull_requests")
    review_reports = relationship(
        "ReviewReport",
        back_populates="pull_request",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("repository_id", "pr_number", name="uq_repo_pr_number"),
    )
