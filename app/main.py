"""Punto de entrada de la aplicación FastAPI."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.cache.memory import InMemoryTTLCache
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.routers import cedula, health


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Inicializa la caché compartida al arrancar y la libera al apagar."""
    configure_logging(settings.log_level)
    app.state.cache = InMemoryTTLCache()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Verificador de Cédula Venezolana",
        description=(
            "Servicio que consulta la información básica de una persona "
            "dado su número de cédula de identidad venezolana.\n\n"
            "⚠️ **Advertencia legal**: este servicio accede a datos de carácter "
            "personal (PII). Úselo en cumplimiento de la legislación de protección "
            "de datos aplicable y respetando los términos de servicio de la fuente."
        ),
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET"],
        allow_headers=["X-API-Key", "Content-Type"],
    )

    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(cedula.router, prefix="/api/v1")

    return app


app = create_app()
