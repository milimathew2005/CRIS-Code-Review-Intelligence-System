# CRIS Cloud Deployment Guide

This document outlines the step-by-step procedure to deploy the **Code Review Intelligence System (CRIS)** backend and frontend services to production using **Neon PostgreSQL**, **Google Cloud Run**, and **Streamlit Community Cloud**.

---

## 1. Database Deployment (Neon PostgreSQL)

Neon is a serverless PostgreSQL platform. To set up your production database:

1. **Create an Account**: Go to [Neon.tech](https://neon.tech/) and sign up.
2. **Initialize a Project**: Create a new project, select PostgreSQL version 15 or 16, and select your preferred region (e.g. `us-east-1`).
3. **Obtain Connection String**: 
   - Neon will provide a connection string. Copy the string.
   - Example connection string:
     ```
     postgresql://alex:passwd@ep-cool-darkness-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
     ```
   - Ensure `?sslmode=require` is appended to the connection string to establish secure socket connection sessions.
4. **Initialize Schema Tables**:
   - Run the API test suite locally or run uvicorn locally pointing to the Neon `DATABASE_URL` once to trigger SQLAlchemy's schema definitions initialization (`Base.metadata.create_all`).
   - Alternatively, use Alembic migrations to upgrade the schema (refer to [architecture.md](architecture.md#4-deployment-guide)).

---

## 2. Backend Deployment (Google Cloud Run)

Google Cloud Run is a serverless container hosting platform. The backend utilizes `backend.Dockerfile` to containerize the FastAPI app.

### Prerequisites
- Install [Google Cloud SDK](https://cloud.google.com/sdk).
- Authenticate and select your Google Cloud project:
  ```bash
  gcloud auth login
  gcloud config set project [YOUR_PROJECT_ID]
  ```

### Step-by-Step Deployment
1. **Enable Google APIs**: Ensure Cloud Build and Cloud Run APIs are enabled:
   ```bash
   gcloud services enable builds.googleapis.com run.googleapis.com
   ```
2. **Submit Container Image**: Build the image using Google Cloud Build and save it to Artifact Registry:
   ```bash
   gcloud builds submit --tag gcr.io/[YOUR_PROJECT_ID]/cris-backend -f backend.Dockerfile .
   ```
3. **Deploy Container to Cloud Run**:
   - Start the container deployment:
     ```bash
     gcloud run deploy cris-backend \
       --image gcr.io/[YOUR_PROJECT_ID]/cris-backend \
       --platform managed \
       --region us-central1 \
       --allow-unauthenticated \
       --set-env-vars="DATABASE_URL=postgresql://alex:passwd@ep-cool-darkness-123456.us-east-2.aws.neon.tech/neondb?sslmode=require" \
       --set-env-vars="GEMINI_API_KEY=your_actual_gemini_api_key" \
       --set-env-vars="GITHUB_TOKEN=your_github_personal_access_token" \
       --set-env-vars="GITHUB_WEBHOOK_SECRET=your_configured_webhook_secret_here"
     ```
4. **Record the Backend Service URL**:
   - Once completed, the CLI will output the Service URL:
     ```
     Service [cris-backend] revision [cris-backend-00001] has been deployed and is serving 100% of traffic.
     URL: https://cris-backend-xxxxxx-uc.a.run.app
     ```
   - Note down this URL. Your API router endpoints will be accessible at: `https://cris-backend-xxxxxx-uc.a.run.app/api/v1`

---

## 3. Frontend Deployment (Streamlit Community Cloud)

Streamlit Community Cloud hosts Streamlit dashboard applications directly from public GitHub repositories.

1. **Commit and Push Code**: Commit all changes (including `frontend/app.py`, `backend.Dockerfile`, and config files) and push them to your public GitHub repository:
   ```bash
   git add .
   git commit -m "deploy: setup docker configurations and Cloud environment variables"
   git push origin main
   ```
2. **Access Streamlit Share**: Go to [share.streamlit.io](https://share.streamlit.io/) and log in using your GitHub account.
3. **Create a New App**:
   - Click the **"New App"** button.
   - Choose your repository: `[YOUR_USERNAME]/CRIS-Code-Review-Intelligence-System`
   - Select Branch: `main`
   - Main file path: `frontend/app.py`
4. **Configure Secrets & Env Variables**:
   - Before deploying, click **"Advanced settings..."** at the bottom of the dialog.
   - In the **Secrets** text area, define the target backend URL using TOML format:
     ```toml
     BACKEND_API_URL = "https://cris-backend-xxxxxx-uc.a.run.app/api/v1"
     ```
   - Save the settings.
5. **Deploy**: Click **"Deploy"**. Streamlit will provision the container, install dependencies from `requirements.txt`, and host your dashboard on a public URL.

---

## 4. Webhook Setup on GitHub

To trigger automated reviews on pull requests:

1. Go to your target GitHub repository, click **Settings** -> **Webhooks** -> **Add Webhook**.
2. **Payload URL**: Enter your Cloud Run backend webhook endpoint:
   ```
   https://cris-backend-xxxxxx-uc.a.run.app/api/v1/webhook/github
   ```
3. **Content type**: Select `application/json`.
4. **Secret**: Enter the exact same string value defined in your backend `GITHUB_WEBHOOK_SECRET` environment variable.
5. **Which events**: Select **"Let me select individual events"** and check **"Pull requests"**. Uncheck all other events to limit load.
6. **Active**: Check the box and click **Add Webhook**.

---

## 5. Security & Access Configurations

1. **API Keys**: Keep `GEMINI_API_KEY` and `GITHUB_TOKEN` secret. For staging setups, pass env-vars directly via Cloud Run console. In production, utilize **Google Cloud Secret Manager** to mount keys securely inside container runtimes.
2. **FastAPI CORS Origins**: Currently, CORS is configured with `allow_origins=["*"]` in `backend/app/main.py`. For secure production deployments, edit `main.py` to specify the exact URL of your Streamlit frontend dashboard instead of the wildcard.
3. **HMAC Signature Checks**: Ensure signature checks are active by maintaining a non-default `GITHUB_WEBHOOK_SECRET`. This prevents malicious actors from triggering fake review invocations.
