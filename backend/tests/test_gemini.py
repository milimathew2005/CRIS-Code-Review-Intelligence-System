import pytest
import json
from unittest.mock import MagicMock
from backend.app.services.context_builder import ContextBuilder
from backend.app.services.gemini_service import GeminiReviewService
from backend.app.schemas.diff import FileDiffSummary, LineChange
from backend.app.schemas.ast import ASTExtractionReport, FunctionContext
from backend.app.schemas.review import ReviewReport

def test_context_builder_packaging():
    """
    Verifies that the ContextBuilder consolidates diff summaries and AST contexts into the prompt context payload.
    """
    file_diff = FileDiffSummary(
        file="auth.py",
        status="modified",
        additions=2,
        deletions=0,
        added_lines=[LineChange(line_number=5, content="user = get_session()")],
        removed_lines=[],
        hunks=[]
    )
    
    ast_report = ASTExtractionReport(
        file="auth.py",
        functions=[
            FunctionContext(
                name="login",
                class_name="AuthService",
                start_line=1,
                end_line=10,
                arguments=["self", "user"],
                return_annotation="bool",
                function_calls=["get_session"],
                variables=["user"],
                imported_modules=[],
                inside_try_block=False,
                inside_loop=False,
                inside_conditional=True
            )
        ]
    )
    
    context = ContextBuilder.build_file_context(file_diff, ast_report)
    
    assert context["file"] == "auth.py"
    assert context["additions_count"] == 2
    assert len(context["added_lines"]) == 1
    assert context["added_lines"][0]["line_number"] == 5
    
    assert len(context["impacted_functions"]) == 1
    func = context["impacted_functions"][0]
    assert func["function_name"] == "login"
    assert func["class_name"] == "AuthService"
    assert func["arguments"] == ["self", "user"]
    assert func["inside_conditional"] is True

def test_gemini_service_valid_response(monkeypatch):
    """
    Verifies that GeminiReviewService correctly executes generation requests, enforcing Pydantic validation.
    """
    mock_client = MagicMock()
    mock_response = MagicMock()
    
    # Mocking successful JSON output matching ReviewReport
    mock_response.text = json.dumps({
        "filename": "auth.py",
        "issues": [
            {
                "issue_type": "Security",
                "severity": "Critical",
                "line_number": 5,
                "description": "Hardcoded raw session token usage.",
                "suggested_fix": "Use safe session validation variables instead."
            }
        ]
    })
    
    mock_client.models.generate_content.return_value = mock_response
    
    # Instantiate service and inject mock client
    service = GeminiReviewService(api_key="mock_key")
    service.client = mock_client
    
    dummy_context = {"file": "auth.py", "added_lines": []}
    report = service.generate_code_review(dummy_context)
    
    assert isinstance(report, ReviewReport)
    assert report.filename == "auth.py"
    assert len(report.issues) == 1
    
    issue = report.issues[0]
    assert issue.issue_type == "Security"
    assert issue.severity == "Critical"
    assert issue.line_number == 5
    assert "Hardcoded raw" in issue.description

def test_gemini_service_api_failure_fallback(monkeypatch):
    """
    Verifies that GeminiReviewService handles API connection exceptions gracefully,
    returning structured error issues.
    """
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("API connection timeout error")
    
    service = GeminiReviewService(api_key="mock_key")
    service.client = mock_client
    
    dummy_context = {"file": "auth.py", "added_lines": []}
    report = service.generate_code_review(dummy_context)
    
    assert isinstance(report, ReviewReport)
    assert report.filename == "auth.py"
    assert len(report.issues) == 1
    
    issue = report.issues[0]
    assert issue.issue_type == "Logic"
    assert issue.severity == "High"
    assert "failed: API connection" in issue.description
