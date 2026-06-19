from fastapi import APIRouter
from backend.app.api.v1.endpoints import health, reviews, webhook, analytics

api_router = APIRouter()

# Register endpoint routers
api_router.include_router(health.router, prefix="/system", tags=["system"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(webhook.router, prefix="/webhook", tags=["webhook"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

