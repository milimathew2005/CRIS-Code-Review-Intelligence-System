import logging
from fastapi import APIRouter, Request, Header, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.security import verify_github_signature
from backend.app.schemas.webhook import GitHubPullRequestWebhook

router = APIRouter()
logger = logging.getLogger("cris.webhook")

@router.post("/github", dependencies=[Depends(verify_github_signature)], summary="Ingest GitHub webhook events")
async def handle_github_webhook(
    request: Request,
    x_github_event: str = Header(..., alias="X-GitHub-Event"),
    db: Session = Depends(get_db)
):
    """
    Receives and processes GitHub webhook events.
    Verifies payload signature before execution.
    Filters and processes only 'pull_request' events.
    """
    if x_github_event != "pull_request":
        # Gracefully ignore events that are not related to pull requests
        return {
            "status": "ignored",
            "reason": f"Ignored non-pull_request GitHub event: {x_github_event}"
        }

    try:
        # Load request payload body
        body_json = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON request payload body.")

    try:
        # Parse payload details dynamically using validation schemas
        payload = GitHubPullRequestWebhook(**body_json)
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Webhook pull_request schema validation failed: {str(e)}"
        )

    # Extract target metadata fields
    repo_name = payload.repository.name
    repo_owner = payload.repository.owner.login
    pr_number = payload.pull_request.number
    pr_title = payload.pull_request.title
    pr_author = payload.pull_request.user.login
    pr_url = payload.pull_request.html_url
    action = payload.action

    # Log variables to stdout in the exact requested format
    log_message = (
        f"\n[WEBHOOK RECEIVED]\n"
        f"Repository: {repo_name}\n"
        f"PR #{pr_number}\n"
        f"Title: {pr_title}\n"
        f"Author: {pr_author}\n"
        f"Action: {action}"
    )
    
    # Use standard logging as well as raw print for console capture clarity
    print(log_message)
    logger.info(log_message)

    # Instantiate Diff Retrieval Service and Parser
    from backend.app.services.diff_retrieval import GitHubDiffService
    from backend.app.parsers.diff_parser import DiffParser

    diff_service = GitHubDiffService()
    try:
        # Fetch the unified diff from GitHub
        raw_diff = await diff_service.fetch_pr_diff(
            owner=repo_owner,
            repo=repo_name,
            pr_number=pr_number
        )
        # Parse the raw unified diff
        parser = DiffParser(raw_diff)
        parsed_files = parser.parse()
    except Exception as e:
        logger.error(f"Error fetching or parsing PR diff: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch or parse PR diff from GitHub: {str(e)}"
        )

    # Log structured changes summary
    for f in parsed_files:
        file_log = (
            f"\n[FILE DIFF PARSED]\n"
            f"File: {f.file}\n"
            f"Status: {f.status}\n"
            f"Additions: {f.additions}\n"
            f"Deletions: {f.deletions}\n"
            f"Added Lines: {[l.line_number for l in f.added_lines]}\n"
            f"Removed Lines: {[l.line_number for l in f.removed_lines]}\n"
            f"Hunks: {len(f.hunks)}"
        )
        print(file_log)
        logger.info(file_log)

    # Perform AST Context Extraction for modified Python files
    from backend.app.parsers.ast_parser import ASTParser
    from backend.app.schemas.ast import ASTExtractionReport
    
    ast_reports = []
    
    for f in parsed_files:
        # Only parse python source files that weren't deleted
        if f.file.endswith(".py") and f.status != "deleted":
            try:
                # Fetch full file contents at HEAD commit SHA (fallback to 'main' if not specified)
                ref_sha = payload.pull_request.head.sha if payload.pull_request.head else "main"
                file_content = await diff_service.fetch_file_content(
                    owner=repo_owner,
                    repo=repo_name,
                    path=f.file,
                    ref=ref_sha
                )
                
                # Parse AST
                ast_parser = ASTParser(file_content)
                ast_parser.parse()
                
                # Extract impacted contexts matching added line numbers
                added_line_numbers = [line.line_number for line in f.added_lines]
                report = ast_parser.extract_impacted_contexts(added_line_numbers)
                report.file = f.file
                ast_reports.append(report)
                
                # Log AST details to console
                for func in report.functions:
                    log_ast = (
                        f"\n[AST CONTEXT EXTRACTED]\n"
                        f"File: {report.file}\n"
                        f"Function: {func.name}\n"
                        f"Class: {func.class_name or 'None'}\n"
                        f"Arguments: {func.arguments}\n"
                        f"Calls: {func.function_calls}\n"
                        f"Variables: {func.variables}\n"
                        f"Try Block: {func.inside_try_block}\n"
                        f"Loop: {func.inside_loop}\n"
                        f"Conditional: {func.inside_conditional}"
                    )
                    print(log_ast)
                    logger.info(log_ast)
            except Exception as e:
                logger.error(f"Error extracting AST for {f.file}: {str(e)}")
                ast_reports.append(
                    ASTExtractionReport(file=f.file, functions=[], error=str(e))
                )

    # Orchestrate Context Building and Gemini Review Execution
    from backend.app.services.context_builder import ContextBuilder
    from backend.app.services.gemini_service import GeminiReviewService
    
    gemini_service = GeminiReviewService()
    review_reports = []
    
    for f in parsed_files:
        # Resolve matching AST report or default to an empty report for non-python files
        matching_report = next((r for r in ast_reports if r.file == f.file), None)
        ast_rep = matching_report or ASTExtractionReport(file=f.file, functions=[])
        
        # Build unified context
        file_context = ContextBuilder.build_file_context(f, ast_rep)
        
        # Run AI code review
        report = gemini_service.generate_code_review(file_context)
        review_reports.append(report)
        
        # Log identified issues to console
        for issue in report.issues:
            issue_log = (
                f"\n[REVIEW ISSUE IDENTIFIED]\n"
                f"File: {report.filename}\n"
                f"Type: {issue.issue_type}\n"
                f"Severity: {issue.severity}\n"
                f"Line: {issue.line_number}\n"
                f"Description: {issue.description}\n"
                f"Suggested Fix: {issue.suggested_fix}"
            )
            print(issue_log)
            logger.info(issue_log)

    # Persist code review records to the database using the Repository Service
    from backend.app.services.review_repository import ReviewRepository
    repo_service = ReviewRepository(db)
    
    try:
        # Get or create repository reference
        repo_record = repo_service.get_or_create_repository(
            owner=repo_owner,
            name=repo_name
        )
        # Create or update pull request details
        pr_record = repo_service.create_or_update_pull_request(
            repository_id=repo_record.id,
            pr_number=pr_number,
            title=pr_title,
            author=pr_author,
            action=action,
            github_url=pr_url
        )
        # Save generated file reports and issues
        for report in review_reports:
            repo_service.save_review_report(
                pull_request_id=pr_record.id,
                filename=report.filename,
                issues=report.issues
            )
    except Exception as e:
        logger.error(f"Database persistence failure: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to commit code review findings to database: {str(e)}"
        )

    return {
        "status": "success",
        "message": "Pull request webhook ingested, diff analyzed, and Gemini review generated.",
        "data": {
            "repository": repo_name,
            "owner": repo_owner,
            "number": pr_number,
            "title": pr_title,
            "author": pr_author,
            "url": pr_url,
            "action": action,
            "changes": [f.model_dump() for f in parsed_files],
            "reports": [r.model_dump() for r in review_reports]
        }
    }


