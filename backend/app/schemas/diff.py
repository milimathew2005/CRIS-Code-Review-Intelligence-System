from pydantic import BaseModel, Field
from typing import List, Dict, Any

class LineChange(BaseModel):
    """
    Represents an individual line modification in a diff.
    """
    line_number: int = Field(..., description="The line number of the change.")
    content: str = Field(..., description="The string contents of the modified line.")

class HunkInfo(BaseModel):
    """
    Represents a unified diff hunk summary block.
    """
    source_start: int = Field(..., description="Line number of hunk start in source file.")
    source_length: int = Field(..., description="Range length of hunk in source file.")
    target_start: int = Field(..., description="Line number of hunk start in target file.")
    target_length: int = Field(..., description="Range length of hunk in target file.")
    changed_lines: List[str] = Field(..., description="All lines modified or containing metadata within the hunk.")

class FileDiffSummary(BaseModel):
    """
    Represents metadata and line changes extracted for an individual file.
    """
    file: str = Field(..., description="The name and path of the file.")
    status: str = Field(..., description="File change status: added, deleted, modified, or renamed.")
    additions: int = Field(..., description="Number of lines added.")
    deletions: int = Field(..., description="Number of lines deleted.")
    added_lines: List[LineChange] = Field(default_factory=list, description="Detailed list of added lines.")
    removed_lines: List[LineChange] = Field(default_factory=list, description="Detailed list of removed lines.")
    hunks: List[HunkInfo] = Field(default_factory=list, description="List of hunks parsed from the file patch.")

class PRDiffReport(BaseModel):
    """
    Summarizes the entire pull request changes.
    """
    repository: str = Field(..., description="The repository title.")
    pr_number: int = Field(..., description="The numeric identifier of the pull request.")
    files: List[FileDiffSummary] = Field(default_factory=list, description="Summaries of all files changed.")
