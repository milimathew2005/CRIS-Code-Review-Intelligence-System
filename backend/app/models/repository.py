from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.app.models.base import Base

class Repository(Base):
    """
    SQLAlchemy model representing a GitHub repository.
    """
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    repository_name = Column(String, nullable=False, index=True)
    repository_owner = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Establish one-to-many relationship with PullRequest
    pull_requests = relationship(
        "PullRequest",
        back_populates="repository",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("repository_owner", "repository_name", name="uq_repo_owner_name"),
    )
