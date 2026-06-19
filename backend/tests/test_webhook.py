import hmac
import hashlib
import json
from backend.app.core.config import settings

def test_webhook_valid_signature_pr_event(client, monkeypatch):
    """
    Verifies that a valid HMAC SHA256 signature and pull_request event payload
    are processed successfully, extracting and logging metadata.
    """
    async def mock_fetch_pr_diff(*args, **kwargs):
        return ""
        
    from backend.app.services.diff_retrieval import GitHubDiffService
    monkeypatch.setattr(GitHubDiffService, "fetch_pr_diff", mock_fetch_pr_diff)

    payload_dict = {
        "action": "opened",
        "number": 42,
        "pull_request": {
            "number": 42,
            "title": "Fix memory leak in parser core",
            "user": {
                "login": "mili-dev"
            },
            "html_url": "https://github.com/mili/codereview/pull/42"
        },
        "repository": {
            "name": "codereview",
            "owner": {
                "login": "mili"
            }
        }
    }
    
    # Serialize exact byte payload to sign and send
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
    assert data["data"]["repository"] == "codereview"
    assert data["data"]["owner"] == "mili"
    assert data["data"]["number"] == 42
    assert data["data"]["title"] == "Fix memory leak in parser core"
    assert data["data"]["author"] == "mili-dev"
    assert data["data"]["action"] == "opened"

def test_webhook_invalid_signature(client):
    """
    Verifies that requests with incorrect signature signatures are rejected
    with a 401 Unauthorized status.
    """
    payload_dict = {"action": "opened", "number": 1}
    payload_str = json.dumps(payload_dict)
    
    response = client.post(
        "/api/v1/webhook/github",
        content=payload_str,
        headers={
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": "sha256=invalidhashvalue1234567890",
            "Content-Type": "application/json"
        }
    )
    
    assert response.status_code == 401
    assert "signature mismatch" in response.json()["detail"].lower()

def test_webhook_missing_signature_header(client):
    """
    Verifies that requests lacking the X-Hub-Signature-256 header are rejected
    with a 401 Unauthorized status.
    """
    payload_dict = {"action": "opened", "number": 1}
    payload_str = json.dumps(payload_dict)
    
    response = client.post(
        "/api/v1/webhook/github",
        content=payload_str,
        headers={
            "X-GitHub-Event": "pull_request",
            "Content-Type": "application/json"
        }
    )
    
    assert response.status_code == 401
    assert "signature header is missing" in response.json()["detail"].lower()

def test_webhook_ignored_event(client):
    """
    Verifies that a valid webhook with a non-pull_request event header (e.g. 'ping')
    is accepted but ignored gracefully.
    """
    payload_dict = {"zen": "Keep it simple.", "hook_id": 123456}
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
            "X-GitHub-Event": "ping",
            "X-Hub-Signature-256": f"sha256={signature}",
            "Content-Type": "application/json"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ignored"
    assert "ping" in data["reason"]
