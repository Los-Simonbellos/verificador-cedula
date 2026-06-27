"""Tests del CedulaService — caché hit/miss y propagación de errores."""

import pytest

from app.cache.memory import InMemoryTTLCache
from app.core.exceptions import CedulaNotFoundError, InvalidCedulaFormatError
from app.models.cedula import Persona
from app.services.cedula_service import CedulaService
from app.services.providers.mock import MockCedulaProvider


@pytest.fixture
def service() -> CedulaService:
    return CedulaService(provider=MockCedulaProvider(), cache=InMemoryTTLCache())


class TestCedulaService:
    async def test_consulta_exitosa(self, service: CedulaService):
        resp = await service.consultar("V12345678")
        assert resp.cedula == "12345678"
        assert resp.nacionalidad == "V"
        assert resp.nombre_completo == "JUAN ANDRES CUEVAS RAMIREZ"
        assert resp.primer_nombre == "JUAN"
        assert resp.fuente == "mock"

    async def test_cache_hit(self, service: CedulaService):
        """Segunda llamada debe venir de caché."""
        await service.consultar("V12345678")
        resp = await service.consultar("V12345678")
        assert resp.fuente == "cache"

    async def test_formato_invalido(self, service: CedulaService):
        with pytest.raises(InvalidCedulaFormatError):
            await service.consultar("abc")

    async def test_cedula_not_found(self, service: CedulaService):
        # Números terminados en "0" → simula not-found en el mock
        with pytest.raises(CedulaNotFoundError):
            await service.consultar("V1234560")

    async def test_normaliza_formato_con_guiones(self, service: CedulaService):
        resp = await service.consultar("v-12.345.678")
        assert resp.cedula == "12345678"

    async def test_sin_prefijo_asume_venezolano(self, service: CedulaService):
        resp = await service.consultar("12345678")
        assert resp.nacionalidad == "V"

    async def test_extranjero(self, service: CedulaService):
        resp = await service.consultar("E11223344")
        assert resp.nacionalidad == "E"
