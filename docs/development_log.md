# CRIS Development Log

This document tracks development phases, architectural decisions, and setup logs for the Code Review Intelligence System (CRIS).

---

## Log: 2026-06-19 - Phase 1: Project Setup

### Decisions Made
1. **Repository Layout**:
   - Monorepo structure with split `backend` and `frontend` folders.
   - Restructured parsing layers from `services/` into a dedicated `parsers/` package to separate pure parsing helpers from stateful business services.

2. **Gemini SDK Choice**:
   - Evaluated the legacy `google-generativeai` package against the next-generation `google-genai` SDK.
   - Chose `google-genai` because it features a centralized `Client` constructor pattern, utilizes standard Pydantic models for request/response serialization, supports clean integrations with Vertex AI, and is optimized for the latest Gemini 2.5 Flash models.

3. **Database Approach**:
   - Database layer configured with PostgreSQL + SQLAlchemy.
   - Added standard environment parameter bindings for host, user, password, port, and database name.

### Setup Status
- Created folder structures for frontend, backend, configuration, and documentation.
- Generated skeleton modules for AST parser, diff parser, Gemini execution service, and endpoints.
- Drafted configurations, requirements, and readme instructions.

---

## Log: 2026-06-19 - Phase 2: PR Diff Retrieval & Parsing

### Decisions Made
1. **GitHub Diff Service (`GitHubDiffService`)**:
   - Created a separate retrieval service using `httpx` and the authenticated GitHub REST API.
   - Leveraged custom header `Accept: application/vnd.github.v3.diff` to request unified diff string content directly.

2. **Diff Schema Representation (`diff.py`)**:
   - Outlined Pydantic schemas representing changed files (`FileDiffSummary`), hunks (`HunkInfo`), and specific line changes (`LineChange`).
   - Ensures type-safe representation of diff subsets.

3. **Diff Parsing via `unidiff`**:
   - Replaced skeleton implementation of `DiffParser` with a full, active implementation leveraging the `unidiff` package.
   - Safely parses added lines, removed lines, and coordinates.

### Status
- Successfully implemented config updates, schemas, fetching service, parsing logic, and console logging.
- Unit tests written and verified passing (8 passed total).

---

## Log: 2026-06-19 - Phase 3: AST Context Extraction

### Decisions Made
1. **AST Context schemas (`ast.py`)**:
   - Outlined `FunctionContext` schema storing variables, function calls, arguments, imports, returns, and structural containment states.
   - Outlined `ASTExtractionReport` mapping errors and file details.

2. **AST Parser Engine (`ast_parser.py`)**:
   - Replaced structural skeleton with standard Python `ast` parsing logic.
   - Designed custom `ASTContextExtractor` visitor to traverse class and function nodes to capture attributes.
   - Implemented line boundary checks: matches lines from diff parser against `[start_line, end_line]` function definitions to isolate impacted elements.
   - Implemented subblock traversal checking if impacted line locations fall inside `ast.Try`, `ast.For`, `ast.While`, or `ast.If` block scopes.

3. **Content Fetching Integration**:
   - Implemented `fetch_file_content` in `GitHubDiffService` utilizing GitHub REST API to get full source code of modified files at specific head commit refs.
   - Allowed backwards compatibility in schemas: made `head` parameter optional in pull request webhooks to avoid breaking previous phase payloads.

### Status
- AST Context extraction and line containment calculations fully operational.
- Test suite successfully upgraded with mock AST parsers and syntax check runs (11 passed total).

---

## Log: 2026-06-19 - Phase 4: Gemini Review Integration

### Decisions Made
1. **Review schemas (`review.py`)**:
   - Upgraded review schemas to specify structural enum/literal types: `IssueTypeType` (Security, Logic, Performance, Style) and `SeverityType` (Critical, High, Medium, Low).
   - Structured JSON validation models defined: `ReviewIssue` and `ReviewReport` wrapping individual findings.

2. **Context Builder service (`context_builder.py`)**:
   - Isolated logic assembling Diff modifications (added/removed lines) and AST parameters (arguments, return signatures, calls, variables, block scopes) into a single unified context dictionary.

3. **Gemini Review service (`gemini_service.py`)**:
   - Fully implemented `GeminiReviewService` wrapping the modern `google-genai` client model call.
   - Enforces Pydantic responses using `response_schema=ReviewReport` and `response_mime_type="application/json"` parameters to ensure structural validation at the API network boundary.
   - Low temperature parameters (0.1) configured to limit creative hallucinations.
   - Stateless fallback warning checks implemented for keyless local executions.

### Status
- End-to-end webhook integration triggers diff parsing, AST extracting, context building, and Gemini structured analysis.
- Full unit tests added with mock clients (14 passed total).

---

## Log: 2026-06-19 - Phase 5: Database Persistence

### Decisions Made
1. **Database Schema Design**:
   - Implemented relational tables in SQLAlchemy matching the spec: `repositories`, `pull_requests`, `review_reports`, and `review_issues`.
   - Setup Cascade relationships (`cascade="all, delete-orphan"`) so that deleting a repository cleans up its child records completely.
   - Enforced UniqueConstraint on `uq_repo_pr_number` to prevent duplicate PR records.

2. **Decoupled Service Layer (`ReviewRepository`)**:
   - Isolated SQL execution from route handlers into `review_repository.py`.
   - Automatically handles upserting pull requests: updates title, author, action, and URL if matching record is present, and logs history as fresh file reports.

3. **API Integration**:
   - Webhook controller receives the db session dependency (`Depends(get_db)`) and executes CRUD operations inside the ingestion handler, mapping reviews securely.

### Status
- Database persistence is fully complete.
- Integration test suite successfully expanded verifying constraints, cascades, and CRUD logic (18 passed total).

---

## Log: 2026-06-19 - Phase 6: Visualization and Analytics

### Decisions Made
1. **Decoupled API Design**:
   - Chose to separate the frontend Streamlit dashboard from the SQLAlchemy database layer entirely by routing all data queries through new FastAPI endpoints (`/api/v1/analytics/*`).
   - Ensures clean separation of concerns and allows Streamlit to act as a pure client application.

2. **Aggregated Service (AnalyticsService)**:
   - Built a dedicated helper service calculating overview counts, repo/PR listings, detailed PR reviews, issue categories, severity distribution, date-based trends, and top problematic repositories.

3. **Streamlit Component Visualizations**:
   - Designed 6 tabs including a Review Sandbox for testing and 5 analytics dashboard tabs.
   - Used Streamlit KPI metric cards with custom HSL-tailored CSS, standard `st.bar_chart` and `st.line_chart` components, and Altair pie/arc charts for category and severity distributions.
   - Built resilient HTTP fallback wrappers in Streamlit so the UI continues displaying high-fidelity mock data if the backend server is unreachable.

### Status
- Successfully built, tested, and verified the visualization layout and analytics APIs.
- Completed automated checks running pytest (all 23 tests passing).
- Completed manual verification checking all dashboard pages in a real browser using a subagent, confirming beautiful rendering and correct interaction behavior.




