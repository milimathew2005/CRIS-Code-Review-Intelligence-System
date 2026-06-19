from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter()

@router.get("/overview", summary="Get simple card-level KPI statistics")
def get_overview(db: Session = Depends(get_db)):
    return AnalyticsService.get_overview_stats(db)

@router.get("/repositories", summary="Get list of all repositories")
def get_repositories(db: Session = Depends(get_db)):
    return AnalyticsService.get_repositories(db)

@router.get("/repositories/{repo_id}/pulls", summary="Get list of pull requests in repository")
def get_repo_pulls(repo_id: int, db: Session = Depends(get_db)):
    return AnalyticsService.get_repository_pulls(db, repo_id)

@router.get("/pulls/{pr_id}", summary="Get detailed file reviews and issues for a PR")
def get_pr_details(pr_id: int, db: Session = Depends(get_db)):
    details = AnalyticsService.get_pr_details(db, pr_id)
    if not details:
        raise HTTPException(status_code=404, detail="Pull request details not found.")
    return details

@router.get("/issues", summary="Get issues counts by category type")
def get_issues_stats(db: Session = Depends(get_db)):
    return AnalyticsService.get_issue_type_stats(db)

@router.get("/severities", summary="Get issues counts by severity levels")
def get_severities_stats(db: Session = Depends(get_db)):
    return AnalyticsService.get_severity_stats(db)

@router.get("/trends", summary="Get date-grouped issue timelines and top problem repos")
def get_trends_stats(db: Session = Depends(get_db)):
    return AnalyticsService.get_trends(db)
