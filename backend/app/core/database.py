from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.core.config import settings

# Engine configuration with pooling features
engine = create_engine(
    settings.database_url, 
    pool_pre_ping=True  # Verifies connection health before using
)

# Declarative session class factory
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

def get_db():
    """
    Dependency injection generator helper to manage transactional session lifetimes.
    Yields database sessions and ensures connection cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
