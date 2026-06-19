from pydantic import BaseModel, Field
from typing import List, Optional, Literal

# Enforcing strict allowed categories and severities via Pydantic Literal typings
IssueTypeType = Literal["Security", "Logic", "Performance", "Style"]
SeverityType = Literal["Critical", "High", "Medium", "Low"]

class ReviewRequest(BaseModel):
    """
    Schema validating the payload for a new manual code review request.
    """
    file_content: str = Field(..., description="The full source code of the file to review.")
    diff_content: Optional[str] = Field(None, description="The Git unified diff string associated with changes.")

class ReviewIssue(BaseModel):
    """
    Pydantic schema representing an individual review issue identified by the AI review engine.
    """
    issue_type: IssueTypeType = Field(..., description="The classification category of the issue.")
    severity: SeverityType = Field(..., description="The impact severity of the finding.")
    line_number: int = Field(..., description="The target line number of the code change containing the issue.")
    description: str = Field(..., description="Details and explanation of the issue.")
    suggested_fix: str = Field(..., description="Concrete code or refactoring recommendation to fix it.")

class ReviewReport(BaseModel):
    """
    Structured code review report wrapper for an individual file.
    """
    filename: str = Field(..., description="Target file name that was reviewed.")
    issues: List[ReviewIssue] = Field(default_factory=list, description="List of identified issues.")

class ReviewResponse(BaseModel):
    """
    Schema defining the wrapper response returned by CRIS backend endpoints.
    """
    summary: str = Field(..., description="Overall summary of structural and semantic findings.")
    reports: List[ReviewReport] = Field(default_factory=list, description="Array of file-level review reports.")
    issues: Optional[List[dict]] = Field(None, description="Backwards compatible issues placeholder.")
