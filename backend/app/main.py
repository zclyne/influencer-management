from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import validation_exception_handler
from app.api.routes import (
    brands,
    campaigns,
    deals,
    email_context,
    exports,
    files,
    health,
    influencer_ingestion,
    influencers,
    jobs,
    outreach,
)
from app.core.config import get_settings
from app.core.logging import configure_logging, log_startup


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        log_startup(settings)
        yield

    app = FastAPI(
        title="Desktop IRM API",
        version="0.1.0",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(influencers.router, prefix="/api/v1")
    app.include_router(influencer_ingestion.router, prefix="/api/v1")
    app.include_router(brands.router, prefix="/api/v1")
    app.include_router(campaigns.router, prefix="/api/v1")
    app.include_router(deals.router, prefix="/api/v1")
    app.include_router(jobs.router, prefix="/api/v1")
    app.include_router(files.router, prefix="/api/v1")
    app.include_router(exports.router, prefix="/api/v1")
    app.include_router(email_context.router, prefix="/api/v1")
    app.include_router(outreach.router, prefix="/api/v1")

    return app


app = create_app()
