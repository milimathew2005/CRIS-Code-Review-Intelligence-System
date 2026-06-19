from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.core.database import get_db

router = APIRouter()

@router.get("/health", summary="Check API and database health status")
def health_check(db: Session = Depends(get_db)):
    """
    Performs validation checks against system resources to assess status.
    Raises a 503 HTTP exception if database connection fails.
    """
    try:
        # Executes a lightweight query against PostgreSQL to check connection integrity
        db.execute(text("SELECT 1"))
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database connectivity health check failed: {str(e)}"
        )
        
    return {
        "status": "online",
        "database": "connected"
    }
