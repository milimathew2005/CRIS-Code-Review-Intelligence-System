import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.repository import Repository
from backend.app.models.pull_request import PullRequest
from backend.app.models.review_report import ReviewReport
from backend.app.models.review_issue import ReviewIssue as ReviewIssueModel
from backend.app.schemas.review import ReviewIssue as ReviewIssueSchema

logger = logging.getLogger("cris.review_repository")

class ReviewRepository:
    """
    Service repository layer isolating SQL query operations from the controller/webhook routes.
    Manages database transactions for CRIS entities.
    """
    
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_repository(self, owner: str, name: str) -> Repository:
        """
        Retrieves a Repository record matching the owner and name, or creates a new one if it does not exist.
        """
        repo = self.db.query(Repository).filter(
            Repository.repository_owner == owner,
            Repository.repository_name == name
        ).first()

        if not repo:
            logger.info(f"Creating new Repository record: {owner}/{name}")
            repo = Repository(
                repository_owner=owner,
                repository_name=name
            )
            self.db.add(repo)
            self.db.commit()
            self.db.refresh(repo)
        return repo

    def create_or_update_pull_request(
        self,
        repository_id: int,
        pr_number: int,
        title: str,
        author: str,
        action: str,
        github_url: str
    ) -> PullRequest:
        """
        Retrieves a PullRequest record matching repository_id and pr_number.
        If it exists: updates its metadata fields (title, action, github_url).
        If it does not exist: creates a new PullRequest record.
        """
        pr = self.db.query(PullRequest).filter(
            PullRequest.repository_id == repository_id,
            PullRequest.pr_number == pr_number
        ).first()

        if pr:
            logger.info(f"Updating existing PullRequest record #{pr_number} metadata")
            pr.title = title
            pr.author = author
            pr.action = action
            pr.github_url = github_url
            self.db.add(pr)
            self.db.commit()
            self.db.refresh(pr)
        else:
            logger.info(f"Creating new PullRequest record #{pr_number}")
            pr = PullRequest(
                repository_id=repository_id,
                pr_number=pr_number,
                title=title,
                author=author,
                action=action,
                github_url=github_url
            )
            self.db.add(pr)
            self.db.commit()
            self.db.refresh(pr)
        return pr

    def save_review_report(
        self,
        pull_request_id: int,
        filename: str,
        issues: List[ReviewIssueSchema]
    ) -> ReviewReport:
        """
        Creates a new ReviewReport session record for a file and maps its list of parsed issues.
        """
        logger.info(f"Saving review report for file: {filename} under PR id {pull_request_id}")
        report = ReviewReport(
            pull_request_id=pull_request_id,
            filename=filename
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)

        # Loop and save corresponding issues
        for issue in issues:
            issue_model = ReviewIssueModel(
                review_report_id=report.id,
                issue_type=issue.issue_type,
                severity=issue.severity,
                line_number=issue.line_number,
                description=issue.description,
                suggested_fix=issue.suggested_fix
            )
            self.db.add(issue_model)
        
        self.db.commit()
        self.db.refresh(report)
        return report
