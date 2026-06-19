import pytest
from backend.app.models.repository import Repository
from backend.app.models.pull_request import PullRequest
from backend.app.models.review_report import ReviewReport
from backend.app.models.review_issue import ReviewIssue as ReviewIssueModel
from backend.app.services.review_repository import ReviewRepository
from backend.app.schemas.review import ReviewIssue as ReviewIssueSchema

def test_repository_and_pr_relationship(db_session):
    """
    Verifies that Repository and PullRequest models write and relate correctly.
    """
    repo = Repository(repository_owner="mili", repository_name="test-repo")
    db_session.add(repo)
    db_session.commit()
    
    pr = PullRequest(
        repository_id=repo.id,
        pr_number=1,
        title="Initial commit PR",
        author="mili-dev",
        action="opened",
        github_url="https://github.com/mili/test-repo/pull/1"
    )
    db_session.add(pr)
    db_session.commit()
    
    # Assert relationship loading
    db_session.refresh(repo)
    assert len(repo.pull_requests) == 1
    assert repo.pull_requests[0].title == "Initial commit PR"
    assert repo.pull_requests[0].repository.repository_name == "test-repo"

def test_cascade_delete_behavior(db_session):
    """
    Verifies that deleting a Repository cascadingly deletes its Pull Requests,
    Review Reports, and Review Issues.
    """
    repo = Repository(repository_owner="mili", repository_name="test-repo-cascade")
    db_session.add(repo)
    db_session.commit()
    
    pr = PullRequest(
        repository_id=repo.id,
        pr_number=12,
        title="Check deletions",
        author="mili-dev",
        action="opened",
        github_url="https://github.com/mili/test-repo-cascade/pull/12"
    )
    db_session.add(pr)
    db_session.commit()
    
    report = ReviewReport(pull_request_id=pr.id, filename="auth.py")
    db_session.add(report)
    db_session.commit()
    
    issue = ReviewIssueModel(
        review_report_id=report.id,
        issue_type="Style",
        severity="Low",
        line_number=5,
        description="Fix PEP8 spacing.",
        suggested_fix="Format line."
    )
    db_session.add(issue)
    db_session.commit()
    
    # Verify everything exists
    assert db_session.query(PullRequest).filter_by(id=pr.id).count() == 1
    assert db_session.query(ReviewReport).filter_by(id=report.id).count() == 1
    assert db_session.query(ReviewIssueModel).filter_by(id=issue.id).count() == 1
    
    # Delete Repository
    db_session.delete(repo)
    db_session.commit()
    
    # Assert everything cascadingly disappeared
    assert db_session.query(PullRequest).filter_by(id=pr.id).count() == 0
    assert db_session.query(ReviewReport).filter_by(id=report.id).count() == 0
    assert db_session.query(ReviewIssueModel).filter_by(id=issue.id).count() == 0

def test_review_repository_crud_operations(db_session):
    """
    Verifies get_or_create_repository and create_or_update_pull_request services logic.
    """
    repo_service = ReviewRepository(db_session)
    
    # 1. Test get_or_create_repository
    repo1 = repo_service.get_or_create_repository(owner="mili", name="repo-crud")
    repo2 = repo_service.get_or_create_repository(owner="mili", name="repo-crud")
    
    # Ensure it retrieved same record, not duplicate
    assert repo1.id == repo2.id
    assert db_session.query(Repository).count() == 1
    
    # 2. Test create_or_update_pull_request (Insert)
    pr1 = repo_service.create_or_update_pull_request(
        repository_id=repo1.id,
        pr_number=5,
        title="Feature A",
        author="dev1",
        action="opened",
        github_url="https://github.com/mili/repo-crud/pull/5"
    )
    
    # 3. Test create_or_update_pull_request (Update - Duplicate prevention check)
    pr2 = repo_service.create_or_update_pull_request(
        repository_id=repo1.id,
        pr_number=5,
        title="Feature A (Updated Title)",
        author="dev1",
        action="synchronize",
        github_url="https://github.com/mili/repo-crud/pull/5"
    )
    
    assert pr1.id == pr2.id
    assert pr2.title == "Feature A (Updated Title)"
    assert pr2.action == "synchronize"
    assert db_session.query(PullRequest).count() == 1

def test_save_review_report_with_issues(db_session):
    """
    Verifies saving review reports and mapping issues correctly.
    """
    repo_service = ReviewRepository(db_session)
    repo = repo_service.get_or_create_repository(owner="mili", name="repo-report")
    pr = repo_service.create_or_update_pull_request(
        repository_id=repo.id,
        pr_number=1,
        title="PR 1",
        author="dev",
        action="opened",
        github_url="https://github.com/mili/repo-report/pull/1"
    )
    
    issues_schemas = [
        ReviewIssueSchema(
            issue_type="Security",
            severity="Critical",
            line_number=12,
            description="Leaked API Key",
            suggested_fix="Move to env."
        ),
        ReviewIssueSchema(
            issue_type="Performance",
            severity="High",
            line_number=20,
            description="Unclosed file",
            suggested_fix="Use context manager."
        )
    ]
    
    report = repo_service.save_review_report(
        pull_request_id=pr.id,
        filename="app.py",
        issues=issues_schemas
    )
    
    assert report.filename == "app.py"
    db_session.refresh(report)
    assert len(report.issues) == 2
    assert report.issues[0].issue_type == "Security"
    assert report.issues[1].issue_type == "Performance"
