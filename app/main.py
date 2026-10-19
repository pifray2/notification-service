from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import setup_logging
from app.integrations.consumer import NotificationConsumer


settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator:
    consumer = NotificationConsumer()
    await consumer.start()
    try:
        yield
    finally:
        await consumer.stop()

    
def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(
        title="Notification for crm project",
        version="0.1.0",
        docs_url="/docs",
        openapi_url= "/openapi.json",
        lifespan=lifespan,
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    app.include_router(api_router)
    return app


app = create_app()