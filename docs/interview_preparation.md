# CRIS Interview Preparation Guide

This guide contains 10 deep technical questions and comprehensive, production-grade answers about the design, implementation, and engineering trade-offs of the **Code Review Intelligence System (CRIS)**.

---

### Q1: Why is it critical that the Streamlit frontend does not query the database directly? How is decoupling enforced in CRIS?
**Answer:**
Direct database access from a frontend client creates tight coupling, increases security vulnerability surfaces (by exposing DB credentials to frontend runtimes), and makes independent updates to frontend or database structures impossible.
In CRIS, **decoupling is strictly enforced**:
- The Streamlit application communicates with the backend exclusively via standard HTTP GET/POST calls to the FastAPI REST API (`/api/v1/analytics/*`).
- Streamlit does not import SQLAlchemy models, nor does it instantiate database sessions. It treats data payloads as pure JSON, which it parses into standard Pandas DataFrames for plotting.
- **Benefits**:
  - **Security**: The database port is closed to the outside world; only the backend container requires database network access.
  - **Scalability**: If the frontend gets high user traffic, Streamlit nodes can be scaled horizontally without multiplying database connections.
  - **Flexibility**: We can swap out the Streamlit frontend for React, Vue, or a CLI tool without changing a single line of backend logic.

---

### Q2: How does the AST parser map unified diff line changes to Python class and function nodes?
**Answer:**
1. **Source Parsing**: CRIS fetches the full file content of the modified file and parses it into an AST representation using Python’s native `ast.parse(source_code)`.
2. **Visitor Walk**: A custom subclass of `ast.NodeVisitor` traverses the syntax tree, identifying `ast.FunctionDef`, `ast.AsyncFunctionDef`, and `ast.ClassDef` nodes.
3. **Range Identification**: For each function or class node, the parser extracts the exact line boundaries (`node.lineno` to `node.end_lineno`).
4. **Boundary Matching**: The parser checks if any modified lines returned by `unidiff` fall within the `[start, end]` ranges of those classes/functions. If a modified line falls inside the range, that function/class is labeled as "impacted."
5. **Scope Tracing**: The AST visitor continues walking the children of impacted function nodes. It checks if the changed line is enclosed inside control structures (`ast.If`, `ast.For`, `ast.While`, or `ast.Try`). If it is, the code context includes the specific block type, enabling the AI to know if changes happened inside exception-handling logic or loops.

---

### Q3: Explain how signature verification is performed using the `X-Hub-Signature-256` header. Why use `hmac.compare_digest`?
**Answer:**
To verify that incoming webhook requests originate from GitHub and have not been tampered with:
1. GitHub signs the JSON payload string using a shared secret token via HMAC-SHA256 and transmits the signature in the `X-Hub-Signature-256` header.
2. The FastAPI backend reads the raw bytes of the incoming request body.
3. It computes the HMAC-SHA256 signature locally:
   ```python
   computed = "sha256=" + hmac.new(
       secret_key.encode("utf-8"),
       raw_payload_bytes,
       hashlib.sha256
   ).hexdigest()
   ```
4. **Prevention of Timing Attacks**: Instead of checking signature equality via standard operators (`==`), CRIS uses `hmac.compare_digest(computed, received)`. Standard string comparison returns `False` immediately upon the first mismatched byte, allowing attackers to measure request execution times and reconstruct the valid signature byte-by-byte. `compare_digest` runs in **constant time** regardless of where the mismatch occurs, neutralizing timing attack channels.

---

### Q4: How does CRIS handle duplicate webhook payloads (idempotency) and keep database records clean?
**Answer:**
During high load or GitHub API retries, the same webhook event or pull request synchronize action might be delivered multiple times.
1. **Unique Constraint**: We define a unique constraint `uq_repo_pr_number` on the `pull_requests` table on `(repository_id, pr_number)`.
2. **Service Layer Upsert (`ReviewRepository.create_or_update_pull_request`)**:
   - Instead of running a blind `INSERT` which would raise database integrity errors, the repository queries for an existing PR under the same `(repository_id, pr_number)`.
   - If it exists, CRIS updates the existing record (PR Title, Author, Action status, GitHub URL). If it does not exist, a new record is generated.
3. **Report History Management**: When a PR is updated (e.g., new commit pushed), we overwrite previous review reports for the changed files. Since `review_reports` contains a cascade constraint pointing to `pull_requests.id`, updating the PR maintains the integrity of the data while allowing old reports on the same files to be replaced to avoid polluting database storage with out-of-date findings.

---

### Q5: How does the Gemini Review Engine guarantee that the AI returns structured JSON?
**Answer:**
Relying on prompt formatting like "Respond in JSON" is fragile; LLMs can still return markdown blocks or invalid structures.
CRIS guarantees structured output at the API boundary using native features of the modern `google-genai` SDK:
1. **Response Schema Configuration**: We declare structural constraints using Pydantic classes:
   ```python
   from pydantic import BaseModel, Field

   class Issue(BaseModel):
       issue_type: str
       severity: str
       line_number: int
       description: str
       suggested_fix: str

   class ReviewReport(BaseModel):
       filename: str
       issues: list[Issue]
   ```
2. **Client Call Binding**: We pass the Pydantic schema and the JSON mime-type directly to the API call:
   ```python
   config = types.GenerateContentConfig(
       response_mime_type="application/json",
       response_schema=ReviewReport,
       temperature=0.1
   )
   response = client.models.generate_content(
       model="gemini-2.5-flash",
       contents=prompt,
       config=config
   )
   ```
3. **Low Temperature**: Enforcing `temperature=0.1` focuses the model on structured code logic review and restricts creative fluctuations (hallucinations), ensuring parsing stability.

---

### Q6: How do you handle database date-groupings compatibly across both SQLite and PostgreSQL?
**Answer:**
Grouping records by day for trend analytics can result in database incompatibilities:
- PostgreSQL uses `func.date(PullRequest.created_at)` or `date_trunc('day', ...)`.
- SQLite does not have a native `date_trunc` function and stores dates as text, requiring `func.date(...)` or custom date text format extractions.
- **Solution**:
  In [analytics_service.py](file:///c:/Users/milim/Desktop/codereview/backend/app/services/analytics_service.py), we utilize the standard SQLAlchemy construct `func.date(Model.created_at).label("date")`.
  - Since SQLAlchemy compiles `func.date()` into the correct SQL Dialect function at runtime (representing `DATE(created_at)` in SQLite and converting timestamps into standard dates in PostgreSQL), it runs successfully in our Pytest SQLite suite and connects to PostgreSQL in production without changes.

---

### Q7: Explain the cascade deletion design of CRIS. What happens when a repository is deleted?
**Answer:**
To prevent orphaned database records and maintain referential integrity, CRIS uses SQLAlchemy's relationship cascades:
```python
# In Repository Model:
pull_requests = relationship(
    "PullRequest", 
    back_populates="repository", 
    cascade="all, delete-orphan"
)
```
- **Execution Flow**:
  - `repositories` is the root model. It has a `one-to-many` relationship with `pull_requests`.
  - `pull_requests` has a `one-to-many` relationship with `review_reports` (with cascade).
  - `review_reports` has a `one-to-many` relationship with `review_issues` (with cascade).
- **Result**:
  If a repository record is deleted via `db.delete(repo)`:
  1. All corresponding `pull_requests` are identified and deleted.
  2. For those pull requests, all associated `review_reports` are purged.
  3. Finally, all related `review_issues` findings are deleted from the database.
  This cascading deletion maintains database cleanups automatically in one single database transaction.

---

### Q8: How does the testing suite prevent test data leakage between test runs?
**Answer:**
We use Pytest fixtures and transactional rollback controls:
1. **Isolated Session Fixture (`db_session`)**:
   - In `backend/tests/conftest.py`, we initialize an in-memory SQLite database (`sqlite:///`) representing a clean slate.
   - For every single test, the fixture yields a separate `Session` object.
2. **Transaction Rollback**:
   - The test session is wrapped inside a database transaction block.
   - Once the test block executes and exits, the fixture calls `session.close()` and drops the temporary tables. No data persists on the filesystem or leaks into subsequent test iterations, ensuring high test independence.

---

### Q9: The current webhook handler runs ast parsing and Gemini API calls synchronously. How would you scale this for production?
**Answer:**
**Problem**: GitHub expects webhook endpoints to respond within 10 seconds. AST parsing and Gemini network API requests can easily take 2-8 seconds. Under concurrent PR pushes, FastAPI requests would queue, leading to webhook timeouts and dropped events.
**Re-architecture Solution**:
- **Asynchronous Task Queue**: Use an asynchronous task worker system like **Celery**, **RQ (Redis Queue)**, or FastAPI’s native `BackgroundTasks`.
- **Flow**:
  1. The FastAPI endpoint parses and validates the webhook signature immediately.
  2. It commits basic repository/PR metadata to the database.
  3. It queues the heavy diff fetching, AST parsing, and Gemini API review task asynchronously:
     ```python
     # Example with FastAPI BackgroundTasks:
     background_tasks.add_task(run_asynchronous_code_review, pr.id, payload)
     ```
  4. The endpoint immediately returns `200 OK` (taking < 50ms).
  5. The background worker processes the queue, queries Gemini, and updates the database records asynchronously.

---

### Q10: What is your API versioning strategy, and how would you roll out a major change?
**Answer:**
CRIS routes all API endpoints under `/api/v1/*` to allow API evolution without breaking existing clients or incoming webhooks.
**Rolling out Version 2**:
1. **Maintain v1**: Keep v1 endpoint directories untouched to handle active webhooks and legacy clients.
2. **Create v2**: Create a parallel routing directory `backend/app/api/v2/` containing the upgraded handlers.
3. **Register v2 Router**: In `backend/app/api/v1/router.py`, include the v2 router under the `/api/v2` prefix:
   ```python
   api_router.include_router(webhook_v2.router, prefix="/v2/webhook")
   ```
4. **Migration**: Update GitHub repository webhook settings to point to the new URL: `/api/v2/webhook/github`. Once all webhook traffic moves to v2, we can deprecate and remove the v1 code modules safely.
