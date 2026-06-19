# CRIS Architecture & Database Layout

This document describes the architectural layout, database models, detailed data sequence flow, and deployment instructions for the Code Review Intelligence System (CRIS).

---

## 1. Architectural Layout

The system is designed with a decoupled architecture to isolate components and ensure backend stability independent of the visualization layer:

```mermaid
graph TD
    GitHub[GitHub Webhook Trigger] -->|POST JSON with HMAC Signature| FastAPI[FastAPI Backend /api/v1/webhook/github]
    FastAPI -->|Extracts metadata & retrieves diff| DiffParser[Diff Parser Engine]
    FastAPI -->|Retrieves full code & extracts ast| ASTParser[AST Scope Extractor]
    FastAPI -->|Combines Context & prompts| GeminiService[Gemini Review Engine]
    GeminiService -->|Structured Call| GeminiAPI[Gemini 2.5 Flash Model]
    GeminiAPI -->|Structured JSON Response| GeminiService
    GeminiService -->|Delivers reports| PersistenceService[Database Persistence Layer]
    PersistenceService -->|Writes transactionally| DB[(PostgreSQL DB)]

    Streamlit[Streamlit Frontend Dashboard] -->|HTTP GET Requests| FastAPIAnalytics[FastAPI Analytics Endpoints /api/v1/analytics/*]
    FastAPIAnalytics -->|Aggregations| DB
```

---

## 2. System Flow Sequence Diagram

The sequence diagram below traces the end-to-end lifecycle of a webhook ingestion through parsing, model evaluation, persistence, and client consumption:

```mermaid
sequenceDiagram
    autonumber
    actor GitHub as GitHub Webhook
    participant API as FastAPI Webhook Endpoint
    participant DB as PostgreSQL DB
    participant Diff as Diff Parser (unidiff)
    participant AST as AST Parser (ast)
    participant Gemini as Gemini Review Engine
    participant Client as Streamlit Dashboard

    GitHub->>API: POST /api/v1/webhook/github (Payload & Signature)
    API->>API: Verify X-Hub-Signature-256 (HMAC-SHA256)
    alt Invalid Signature
        API-->>GitHub: 401 Unauthorized
    else Valid Signature
        API->>DB: Upsert Repository & PR Metadata
        API->>Diff: Fetch & Parse unified git diff
        Diff-->>API: List of modified files, hunks, and line ranges
        loop For each modified Python file
            API->>GitHub: Fetch file source content (head ref)
            GitHub-->>API: Source code
            API->>AST: Extract AST metadata matching modified line boundaries
            AST-->>API: Class/function signatures & block containment
            API->>Gemini: Build unified Context (Diff + AST)
            Gemini->>Gemini: Query Gemini 2.5 Flash with structured schema output
            Gemini-->>API: Return structured ReviewReport JSON
            API->>DB: Save ReviewReport and ReviewIssues records
        end
        API-->>GitHub: 200 OK (Event Processed)
    end

    Client->>API: GET /api/v1/analytics/overview
    API->>DB: Query metric aggregates
    DB-->>API: Returns counts
    API-->>Client: Returns JSON response
    Client->>Client: Render dynamic charts (Altair/cards)
```

---

## 3. Database ER Diagram

CRIS persists reviews and findings using PostgreSQL. Below is the Entity Relationship Diagram (ERD) defining the schema, constraints, and relationships:

```mermaid
erDiagram
    REPOSITORIES ||--o{ PULL_REQUESTS : "has"
    PULL_REQUESTS ||--o{ REVIEW_REPORTS : "generates"
    REVIEW_REPORTS ||--o{ REVIEW_ISSUES : "contains"

    REPOSITORIES {
        int id PK
        string repository_owner
        string repository_name
        datetime created_at
    }

    PULL_REQUESTS {
        int id PK
        int repository_id FK
        int pr_number
        string title
        string author
        string action
        string github_url
        datetime created_at
    }

    REVIEW_REPORTS {
        int id PK
        int pull_request_id FK
        string filename
        datetime created_at
    }

    REVIEW_ISSUES {
        int id PK
        int review_report_id FK
        string issue_type
        string severity
        int line_number
        string description
        string suggested_fix
        datetime created_at
    }
```

### Table Schema Details & Rules
1. **`repositories`**:
   - Represents a tracked repository.
   - Cascade delete: Deleting a repository deletes all associated pull requests.
2. **`pull_requests`**:
   - Represents a specific pull request event.
   - Unique constraint: `uq_repo_pr_number` on `(repository_id, pr_number)` ensures unique PR indexing per repository.
3. **`review_reports`**:
   - Stores reviewed files details per PR. One record per file.
4. **`review_issues`**:
   - Holds structured AI code findings.
   - Enforces specific validation parameters:
     - `issue_type`: Allowed values include `Security`, `Logic`, `Performance`, `Style`.
     - `severity`: Allowed values include `Critical`, `High`, `Medium`, `Low`.

---

## 4. Deployment Guide

### A. Production Database Setup (Migrations via Alembic)
For production systems, schema migrations should be managed via Alembic to prevent data loss.

1. **Initialize Alembic**:
   ```bash
   alembic init alembic
   ```
2. **Configure Environment**:
   Update `alembic/env.py` to import models:
   ```python
   from backend.app.models.base import Base
   target_metadata = Base.metadata
   ```
3. **Generate & Run Migrations**:
   ```bash
   # Generate migration script
   alembic revision --autogenerate -m "Add CRIS initial schema"
   
   # Apply migration to PostgreSQL
   alembic upgrade head
   ```

---

## 5. Dockerized Container Setup

To deploy CRIS using Docker containers (PostgreSQL database, FastAPI backend, and Streamlit frontend), use the configuration below.

### 1. [NEW] Dockerfile (Backend)
Create `backend.Dockerfile` in the root:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ /app/backend/
ENV PYTHONPATH=/app

EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. [NEW] Dockerfile (Frontend)
Create `frontend.Dockerfile` in the root:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY frontend/ /app/frontend/

EXPOSE 8501
CMD ["streamlit", "run", "frontend/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
```

### 3. [NEW] docker-compose.yml
Create `docker-compose.yml` in the root:
```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: cris_postgres_db
    environment:
      POSTGRES_DB: ${DB_NAME:-cris_db}
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-postgres}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-postgres} -d ${DB_NAME:-cris_db}"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: backend.Dockerfile
    container_name: cris_fastapi_backend
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - GITHUB_WEBHOOK_SECRET=${GITHUB_WEBHOOK_SECRET}
      - DB_USER=${DB_USER:-postgres}
      - DB_PASSWORD=${DB_PASSWORD:-postgres}
      - DB_HOST=db
      - DB_PORT=5432
      - DB_NAME=${DB_NAME:-cris_db}
    depends_on:
      db:
        condition: service_healthy

  frontend:
    build:
      context: .
      dockerfile: frontend.Dockerfile
    container_name: cris_streamlit_frontend
    ports:
      - "8501:8501"
    environment:
      - BACKEND_API_URL=http://backend:8000/api/v1
    depends_on:
      - backend

volumes:
  postgres_data:
```

Launch the entire stack with:
```bash
docker-compose up --build
```
