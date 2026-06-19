from typing import Dict, Any, List
from unidiff import PatchSet
from backend.app.schemas.diff import FileDiffSummary, LineChange, HunkInfo

class DiffParser:
    """
    Parser wrapper utilizing the `unidiff` package.
    Responsible for:
    - Reading standard unified git diff streams/files.
    - Resolving file names, added lines, modified lines, and line numbers.
    - Grouping code blocks into structures mapping additions and deletions.
    """
    
    def __init__(self, diff_content: str):
        self.diff_content = diff_content

    def parse(self) -> List[FileDiffSummary]:
        """
        Parses diff string using unidiff PatchSet.
        Returns a list of FileDiffSummary models mapping modified lines and file targets.
        """
        if not self.diff_content or not self.diff_content.strip():
            return []

        patch = PatchSet(self.diff_content)
        summaries = []

        for patched_file in patch:
            # Determine file status
            if patched_file.is_added_file:
                status = "added"
            elif patched_file.is_removed_file:
                status = "deleted"
            elif patched_file.is_rename:
                status = "renamed"
            else:
                status = "modified"

            added_lines = []
            removed_lines = []
            hunks = []

            for hunk in patched_file:
                changed_lines = []
                for line in hunk:
                    # Gather string representation of line changes
                    changed_lines.append(str(line))
                    
                    if line.is_added:
                        # For additions, target_line_no represents the line in the new file
                        added_lines.append(
                            LineChange(
                                line_number=line.target_line_no or 0,
                                content=line.value.rstrip("\r\n")
                            )
                        )
                    elif line.is_removed:
                        # For deletions, source_line_no represents the line in the original file
                        removed_lines.append(
                            LineChange(
                                line_number=line.source_line_no or 0,
                                content=line.value.rstrip("\r\n")
                            )
                        )

                hunks.append(
                    HunkInfo(
                        source_start=hunk.source_start or 0,
                        source_length=hunk.source_length or 0,
                        target_start=hunk.target_start or 0,
                        target_length=hunk.target_length or 0,
                        changed_lines=changed_lines
                    )
                )

            summaries.append(
                FileDiffSummary(
                    file=patched_file.path,
                    status=status,
                    additions=patched_file.added,
                    deletions=patched_file.removed,
                    added_lines=added_lines,
                    removed_lines=removed_lines,
                    hunks=hunks
                )
            )

        return summaries
