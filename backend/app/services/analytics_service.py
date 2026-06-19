from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.repository import Repository
from backend.app.models.pull_request import PullRequest
from backend.app.models.review_report import ReviewReport
from backend.app.models.review_issue import ReviewIssue

class AnalyticsService:
    """
    Service responsible for querying database records and computing
    aggregated analytics metrics ready for frontend consumption.
    """
    
    @staticmethod
    def get_overview_stats(db: Session) -> Dict[str, int]:
        """
        Calculates simple KPI metric counts.
        """
        return {
            "total_repositories": db.query(Repository).count(),
            "total_pull_requests": db.query(PullRequest).count(),
            "total_review_reports": db.query(ReviewReport).count(),
            "total_issues_detected": db.query(ReviewIssue).count()
        }

    @staticmethod
    def get_repositories(db: Session) -> List[Dict[str, Any]]:
        """
        Retrieves all repositories.
        """
        repos = db.query(Repository).all()
        return [
            {
                "id": r.id,
                "owner": r.repository_owner,
                "name": r.repository_name,
                "full_name": f"{r.repository_owner}/{r.repository_name}"
            }
            for r in repos
        ]

    @staticmethod
    def get_repository_pulls(db: Session, repository_id: int) -> List[Dict[str, Any]]:
        """
        Retrieves all pull requests belonging to a repository.
        """
        pulls = db.query(PullRequest).filter(
            PullRequest.repository_id == repository_id
        ).all()
        return [
            {
                "id": p.id,
                "pr_number": p.pr_number,
                "title": p.title,
                "author": p.author,
                "action": p.action,
                "github_url": p.github_url
            }
            for p in pulls
        ]

    @staticmethod
    def get_pr_details(db: Session, pr_id: int) -> Dict[str, Any]:
        """
        Retrieves files reviewed, severity stats, and issues list for a PR.
        """
        pr = db.query(PullRequest).filter(PullRequest.id == pr_id).first()
        if not pr:
            return {}

        reports = db.query(ReviewReport).filter(ReviewReport.pull_request_id == pr_id).all()
        report_ids = [r.id for r in reports]
        
        issues = []
        if report_ids:
            issues = db.query(ReviewIssue).filter(
                ReviewIssue.review_report_id.in_(report_ids)
            ).all()

        # Calculate severity distribution
        severity_dist = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for issue in issues:
            if issue.severity in severity_dist:
                severity_dist[issue.severity] += 1

        return {
            "pr_number": pr.pr_number,
            "title": pr.title,
            "author": pr.author,
            "github_url": pr.github_url,
            "files_reviewed": [r.filename for r in reports],
            "total_issues": len(issues),
            "severity_distribution": severity_dist,
            "issues": [
                {
                    "filename": next((r.filename for r in reports if r.id == i.review_report_id), "unknown"),
                    "issue_type": i.issue_type,
                    "severity": i.severity,
                    "line_number": i.line_number,
                    "description": i.description,
                    "suggested_fix": i.suggested_fix
                }
                for i in issues
            ]
        }

    @staticmethod
    def get_issue_type_stats(db: Session) -> Dict[str, int]:
        """
        Calculates issue counts grouped by type (Security, Logic, Performance, Style).
        """
        results = db.query(
            ReviewIssue.issue_type,
            func.count(ReviewIssue.id)
        ).group_by(ReviewIssue.issue_type).all()
        
        stats = {"Security": 0, "Logic": 0, "Performance": 0, "Style": 0}
        for issue_type, count in results:
            if issue_type in stats:
                stats[issue_type] = count
        return stats

    @staticmethod
    def get_severity_stats(db: Session) -> Dict[str, int]:
        """
        Calculates issue counts grouped by severity level (Critical, High, Medium, Low).
        """
        results = db.query(
            ReviewIssue.severity,
            func.count(ReviewIssue.id)
        ).group_by(ReviewIssue.severity).all()
        
        stats = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for severity, count in results:
            if severity in stats:
                stats[severity] = count
        return stats

    @staticmethod
    def get_trends(db: Session) -> Dict[str, Any]:
        """
        Calculates timeline trends: issues created over time, PR reviews over time,
        and top problematic repositories by issue count.
        """
        # Issues over time (grouped by date)
        issues_over_time_query = db.query(
            func.date(ReviewIssue.created_at).label("date"),
            func.count(ReviewIssue.id).label("count")
        ).group_by(func.date(ReviewIssue.created_at)).all()
        
        issues_over_time = [
            {"date": str(row.date), "count": row.count}
            for row in issues_over_time_query
        ]

        # PRs over time (grouped by date)
        prs_over_time_query = db.query(
            func.date(PullRequest.created_at).label("date"),
            func.count(PullRequest.id).label("count")
        ).group_by(func.date(PullRequest.created_at)).all()
        
        prs_over_time = [
            {"date": str(row.date), "count": row.count}
            for row in prs_over_time_query
        ]

        # Problematic repositories: issues per repository owner/name
        problematic_repos_query = db.query(
            Repository.repository_owner,
            Repository.repository_name,
            func.count(ReviewIssue.id).label("issue_count")
        ).join(
            PullRequest, Repository.id == PullRequest.repository_id
        ).join(
            ReviewReport, PullRequest.id == ReviewReport.pull_request_id
        ).join(
            ReviewIssue, ReviewReport.id == ReviewIssue.review_report_id
        ).group_by(
            Repository.repository_owner,
            Repository.repository_name
        ).order_by(
            func.count(ReviewIssue.id).desc()
        ).limit(5).all()

        problematic_repos = [
            {
                "repository": f"{row.repository_owner}/{row.repository_name}",
                "issues": row.issue_count
            }
            for row in problematic_repos_query
        ]

        return {
            "issues_over_time": issues_over_time,
            "prs_over_time": prs_over_time,
            "problematic_repositories": problematic_repos
        }
