import hmac
import hashlib
import json
import pytest
from backend.app.core.config import settings
from backend.app.parsers.diff_parser import DiffParser

# Mock unified diff representation containing additions, deletions, and hunks
SAMPLE_DIFF = (
    "diff --git a/auth.py b/auth.py\n"
    "index 1234567..89abcde 100644\n"
    "--- a/auth.py\n"
    "+++ b/auth.py\n"
    "@@ -1,3 +1,5 @@\n"
    " def login(user, password):\n"
    "-    if user == \"admin\":\n"
    "-        return True\n"
    "+    if user == \"admin\" and password == \"secret\":\n"
    "+        return True\n"
    "+    else:\n"
    "+        return False\n"
)

def test_diff_parser_parsing_logic():
    """
    Validates that the DiffParser correctly parses raw unified diff outputs into structured schemas.
    """
    parser = DiffParser(SAMPLE_DIFF)
    files = parser.parse()
    
    assert len(files) == 1
    file_summary = files[0]
    
    assert file_summary.file == "auth.py"
    assert file_summary.status == "modified"
    assert file_summary.additions == 4
    assert file_summary.deletions == 2
    
    # Asserting removed lines
    assert len(file_summary.removed_lines) == 2
    assert file_summary.removed_lines[0].line_number == 2
    assert file_summary.removed_lines[0].content == '    if user == "admin":'
    assert file_summary.removed_lines[1].line_number == 3
    assert file_summary.removed_lines[1].content == '        return True'
    
    # Asserting added lines
    assert len(file_summary.added_lines) == 4
    assert file_summary.added_lines[0].line_number == 2
    assert file_summary.added_lines[0].content == '    if user == "admin" and password == "secret":'
    assert file_summary.added_lines[1].line_number == 3
    assert file_summary.added_lines[1].content == '        return True'
    assert file_summary.added_lines[2].line_number == 4
    assert file_summary.added_lines[2].content == '    else:'
    assert file_summary.added_lines[3].line_number == 5
    assert file_summary.added_lines[3].content == '        return False'

    # Asserting hunk boundaries
    assert len(file_summary.hunks) == 1
    hunk = file_summary.hunks[0]
    assert hunk.source_start == 1
    assert hunk.source_length == 3
    assert hunk.target_start == 1
    assert hunk.target_length == 5
    assert len(hunk.changed_lines) == 7  # Includes contexts, additions, deletions

def test_webhook_with_mocked_diff_service(client, monkeypatch):
    """
    Verifies that the /webhook/github endpoint orchestrates diff retrieval and parsing.
    Mocks the fetch_pr_diff service to return SAMPLE_DIFF.
    """
    # Mocking fetch_pr_diff call in GitHubDiffService
    async def mock_fetch_pr_diff(*args, **kwargs):
        return SAMPLE_DIFF
        
    async def mock_fetch_file_content(*args, **kwargs):
        return (
            "def login(user, password):\n"
            "    if user == 'admin' and password == 'secret':\n"
            "        return True\n"
            "    else:\n"
            "        return False\n"
        )
        
    from backend.app.services.diff_retrieval import GitHubDiffService
    monkeypatch.setattr(GitHubDiffService, "fetch_pr_diff", mock_fetch_pr_diff)
    monkeypatch.setattr(GitHubDiffService, "fetch_file_content", mock_fetch_file_content)
    
    payload_dict = {
        "action": "opened",
        "number": 12,
        "pull_request": {
            "number": 12,
            "title": "Update login auth verification checks",
            "user": {
                "login": "mili"
            },
            "html_url": "https://github.com/mili/repo/pull/12",
            "head": {
                "sha": "1234567890abcdef"
            }
        },
        "repository": {
            "name": "my-repo",
            "owner": {
                "login": "mili"
            }
        }
    }
    
    payload_str = json.dumps(payload_dict)
    signature = hmac.new(
        key=settings.GITHUB_WEBHOOK_SECRET.encode("utf-8"),
        msg=payload_str.encode("utf-8"),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    response = client.post(
        "/api/v1/webhook/github",
        content=payload_str,
        headers={
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": f"sha256={signature}",
            "Content-Type": "application/json"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "diff analyzed, and gemini review generated" in data["message"].lower()
    
    # Verify parsed changes exist in response body
    changes = data["data"]["changes"]
    assert len(changes) == 1
    assert changes[0]["file"] == "auth.py"
    assert changes[0]["status"] == "modified"
    assert changes[0]["additions"] == 4
    assert len(changes[0]["added_lines"]) == 4
    
    # Verify Review Reports exist (since API credentials are not set in tests, it falls back to configuration warning report)
    reports = data["data"]["reports"]
    assert len(reports) == 1
    assert reports[0]["filename"] == "auth.py"
    assert len(reports[0]["issues"]) == 1
    issue = reports[0]["issues"][0]
    assert issue["issue_type"] == "Style"
    assert issue["severity"] == "Low"
    assert "credentials not configured" in issue["description"].lower()

