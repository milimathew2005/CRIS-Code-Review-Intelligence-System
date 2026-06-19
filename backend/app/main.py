import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.v1.router import api_router
from backend.app.core.config import settings

# Configure basic logging for production visibility
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cris.main")

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
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register v1 endpoints
app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
def startup_event():
    logger.info("CRIS FastAPI Application Starting Up...")
    logger.info(f"Environment: {settings.APP_ENV}")
    try:
        from urllib.parse import urlparse
        parsed = urlparse(settings.database_url)
        logger.info(f"Database Target Host: {parsed.hostname or 'unknown'}")
        logger.info(f"Database Name: {parsed.path.lstrip('/') or 'unknown'}")
    except Exception:
        logger.info("Database Target Host: unable to parse host info safely")

@app.on_event("shutdown")
def shutdown_event():
    logger.info("CRIS FastAPI Application Shutting Down...")

@app.get("/", summary="Root index redirect")
def root_index():
    return {
        "message": "Welcome to CRIS (Code Review Intelligence System) API.",
        "docs_url": "/docs"
    }
