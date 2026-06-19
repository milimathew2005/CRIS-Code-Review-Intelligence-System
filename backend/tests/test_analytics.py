import pytest
from backend.app.models.repository import Repository
from backend.app.models.pull_request import PullRequest
from backend.app.models.review_report import ReviewReport
from backend.app.models.review_issue import ReviewIssue
from backend.app.services.analytics_service import AnalyticsService

@pytest.fixture
def populate_analytics_data(db_session):
    """
    Populates mock repository review data to test aggregations.
    """
    repo = Repository(repository_owner="mili", repository_name="repo-analytics")
    db_session.add(repo)
    db_session.commit()

    pr = PullRequest(
        repository_id=repo.id,
        pr_number=99,
        title="Analytics PR",
        author="analytics-dev",
        action="closed",
        github_url="https://github.com/mili/repo-analytics/pull/99"
    )
    db_session.add(pr)
    db_session.commit()

    report = ReviewReport(pull_request_id=pr.id, filename="main.py")
    db_session.add(report)
    db_session.commit()

    issue1 = ReviewIssue(
        review_report_id=report.id,
        issue_type="Security",
        severity="Critical",
        line_number=10,
        description="Vulnerability found",
        suggested_fix="Fix it"
    )
    issue2 = ReviewIssue(
        review_report_id=report.id,
        issue_type="Logic",
        severity="Medium",
        line_number=20,
        description="Logic error",
        suggested_fix="Fix logic"
    )
    db_session.add(issue1)
    db_session.add(issue2)
    db_session.commit()

    return repo, pr, report

def test_analytics_service_overview_aggregations(db_session, populate_analytics_data):
    """
    Verifies that AnalyticsService computes overview metric counts correctly.
    """
    stats = AnalyticsService.get_overview_stats(db_session)
    assert stats["total_repositories"] == 1
    assert stats["total_pull_requests"] == 1
    assert stats["total_review_reports"] == 1
    assert stats["total_issues_detected"] == 2

def test_analytics_service_selectors_and_details(db_session, populate_analytics_data):
    """
    Verifies that AnalyticsService lists repositories, pulls, and builds detailed PR reports.
    """
    repo, pr, report = populate_analytics_data
    
    # 1. Test get_repositories
    repos = AnalyticsService.get_repositories(db_session)
    assert len(repos) == 1
    assert repos[0]["name"] == "repo-analytics"
    
    # 2. Test get_repository_pulls
    pulls = AnalyticsService.get_repository_pulls(db_session, repo.id)
    assert len(pulls) == 1
    assert pulls[0]["pr_number"] == 99
    
    # 3. Test get_pr_details
    details = AnalyticsService.get_pr_details(db_session, pr.id)
    assert details["pr_number"] == 99
    assert len(details["files_reviewed"]) == 1
    assert details["files_reviewed"][0] == "main.py"
    assert details["severity_distribution"]["Critical"] == 1
    assert details["severity_distribution"]["Medium"] == 1
    assert len(details["issues"]) == 2

def test_analytics_service_issue_distribution_groups(db_session, populate_analytics_data):
    """
    Verifies that AnalyticsService groups issues correctly by type and severity.
    """
    # 1. Test category groups
    categories = AnalyticsService.get_issue_type_stats(db_session)
    assert categories["Security"] == 1
    assert categories["Logic"] == 1
    assert categories["Performance"] == 0
    
    # 2. Test severity groups
    severities = AnalyticsService.get_severity_stats(db_session)
    assert severities["Critical"] == 1
    assert severities["Medium"] == 1
    assert severities["High"] == 0

def test_analytics_service_timelines_and_problematic(db_session, populate_analytics_data):
    """
    Verifies that AnalyticsService correctly maps date groups and top problematic repos.
    """
    trends = AnalyticsService.get_trends(db_session)
    assert len(trends["issues_over_time"]) == 1
    assert trends["issues_over_time"][0]["count"] == 2
    
    assert len(trends["prs_over_time"]) == 1
    assert trends["prs_over_time"][0]["count"] == 1
    
    assert len(trends["problematic_repositories"]) == 1
    assert trends["problematic_repositories"][0]["repository"] == "mili/repo-analytics"
    assert trends["problematic_repositories"][0]["issues"] == 2

def test_analytics_api_endpoints(client, db_session, populate_analytics_data):
    """
    Verifies that FastAPI router endpoints return successful status codes.
    """
    repo, pr, report = populate_analytics_data
    
    # Overview
    r_overview = client.get("/api/v1/analytics/overview")
    assert r_overview.status_code == 200
    assert r_overview.json()["total_repositories"] == 1
    
    # Repositories
    r_repos = client.get("/api/v1/analytics/repositories")
    assert r_repos.status_code == 200
    assert len(r_repos.json()) == 1
    
    # Pulls
    r_pulls = client.get(f"/api/v1/analytics/repositories/{repo.id}/pulls")
    assert r_pulls.status_code == 200
    
    # PR details
    r_details = client.get(f"/api/v1/analytics/pulls/{pr.id}")
    assert r_details.status_code == 200
    assert r_details.json()["pr_number"] == 99
    
    # Trends
    r_trends = client.get("/api/v1/analytics/trends")
    assert r_trends.status_code == 200
