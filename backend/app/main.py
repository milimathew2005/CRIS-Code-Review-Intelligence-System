from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.v1.router import api_router
from backend.app.core.config import settings

# FastAPI Instance Initialization
app = FastAPI(
    title="Code Review Intelligence System (CRIS) API",
    description="Backend services for parsing and AI-powered reviews.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Cross-Origin Resource Sharing (CORS) Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production systems
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register v1 endpoints
app.include_router(api_router, prefix="/api/v1")

@app.get("/", summary="Root index redirect")
def root_index():
    return {
        "message": "Welcome to CRIS (Code Review Intelligence System) API.",
        "docs_url": "/docs"
    }
