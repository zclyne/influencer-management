from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import campaigns, health, influencer_ingestion, influencers
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
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(influencers.router, prefix="/api/v1")
    app.include_router(influencer_ingestion.router, prefix="/api/v1")
    app.include_router(campaigns.router, prefix="/api/v1")

    return app


app = create_app()
