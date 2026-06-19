from typing import Dict, Any, List
from backend.app.schemas.diff import FileDiffSummary
from backend.app.schemas.ast import ASTExtractionReport

class ContextBuilder:
    """
    Component responsible for constructing a consolidated review context block.
    Integrates diff additions/deletions and static AST scope declarations
    to provide the LLM with structured code context prior to prompting.
    """
    
    @staticmethod
    def build_file_context(file_diff: FileDiffSummary, ast_report: ASTExtractionReport) -> Dict[str, Any]:
        """
        Merges Diff coordinates and AST functions data structures.
        """
        functions_meta = []
        for func in ast_report.functions:
            functions_meta.append({
                "function_name": func.name,
                "class_name": func.class_name or "None",
                "arguments": func.arguments,
                "return_annotation": func.return_annotation or "None",
                "variables": func.variables,
                "function_calls": func.function_calls,
                "imported_modules": func.imported_modules,
                "inside_try_block": func.inside_try_block,
                "inside_loop": func.inside_loop,
                "inside_conditional": func.inside_conditional
            })

        return {
            "file": file_diff.file,
            "status": file_diff.status,
            "additions_count": file_diff.additions,
            "deletions_count": file_diff.deletions,
            "added_lines": [
                {"line_number": l.line_number, "content": l.content} for l in file_diff.added_lines
            ],
            "removed_lines": [
                {"line_number": l.line_number, "content": l.content} for l in file_diff.removed_lines
            ],
            "impacted_functions": functions_meta
        }
