from fastapi import APIRouter, HTTPException
from backend.app.schemas.review import ReviewRequest, ReviewResponse

router = APIRouter()

@router.post("/review", response_model=ReviewResponse, summary="Submit code and diff for review")
def submit_review(payload: ReviewRequest):
    """
    Submits code file content and associated diff content to perform reviews.
    Currently operates in skeleton mode.
    """
    # SKELETON: Business flow calling services to be added in future.
    return ReviewResponse(
        summary="Review request received. Backend setup verified successfully.",
        issues=[
            {
                "file_path": "main.py",
                "line_number": 1,
                "severity": "info",
                "message": "Skeleton review placeholder. Setup completed.",
                "code_snippet": None
            }
        ]
    )
