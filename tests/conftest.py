"""Fixtures compartidas de pytest."""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.cache.memory import InMemoryTTLCache
from app.core.config import settings
from app.main import app
from app.routers.cedula import get_cedula_service
from app.services.cedula_service import CedulaService
from app.services.providers.mock import MockCedulaProvider


def _service_factory(cache: InMemoryTTLCache):
    """Crea una función que siempre devuelve el mismo servicio con la caché dada."""
    service = CedulaService(provider=MockCedulaProvider(), cache=cache)
    return lambda: service


@pytest_asyncio.fixture
async def async_client() -> AsyncClient:
    """Cliente autenticado. La caché es compartida entre requests del mismo test."""
    cache = InMemoryTTLCache()
    app.dependency_overrides[get_cedula_service] = _service_factory(cache)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"X-API-Key": settings.api_key},
    ) as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def unauth_client() -> AsyncClient:
    """Cliente sin API Key para probar autenticación."""
    cache = InMemoryTTLCache()
    app.dependency_overrides[get_cedula_service] = _service_factory(cache)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
    app.dependency_overrides.clear()
