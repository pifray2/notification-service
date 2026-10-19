from fastapi import APIRouter

from app.api.routes import health, notifications


api_router = APIRouter()
api_router.include_router(notifications.router)
api_router.include_router(health.router)