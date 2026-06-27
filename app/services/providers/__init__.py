"""Factory de providers de cédula.

Selecciona el provider según settings.provider:
  - "mock" → MockCedulaProvider (sin red, para dev/tests)
  - "pnp"  → PNPScraperProvider (crea su propio httpx.AsyncClient por consulta)
"""

from app.core.config import settings
from app.services.providers.base import CedulaProvider
from app.services.providers.mock import MockCedulaProvider
from app.services.providers.pnp_scraper import PNPScraperProvider


def get_provider() -> CedulaProvider:
    """Retorna el provider configurado por settings.provider."""
    if settings.provider == "pnp":
        return PNPScraperProvider()
    return MockCedulaProvider()
