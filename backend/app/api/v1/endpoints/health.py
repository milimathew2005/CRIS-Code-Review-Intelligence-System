from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.core.database import get_db

router = APIRouter()

@router.get("/health", summary="Check API and database health status")
def health_check(db: Session = Depends(get_db)):
    """
    Performs validation checks against system resources to assess status.
    """
    db_status = "unknown"
    try:
        # Executes a lightweight query against PostgreSQL to check connection integrity
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
        
    return {
        "status": "online",
        "database": db_status
    }
