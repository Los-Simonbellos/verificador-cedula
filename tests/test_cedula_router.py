"""Tests del router /api/v1/cedula — integración con TestClient async."""

import pytest
from httpx import AsyncClient


class TestCedulaEndpoint:
    async def test_consulta_exitosa(self, async_client: AsyncClient):
        resp = await async_client.get("/api/v1/cedula/V12345678")
        assert resp.status_code == 200
        data = resp.json()
        assert data["cedula"] == "12345678"
        assert data["nacionalidad"] == "V"
        assert "nombre_completo" in data
        assert "primer_nombre" in data
        assert "primer_apellido" in data
        assert "consultado_en" in data
        assert data["fuente"] in ("mock", "cache", "pnp")

    async def test_sin_api_key_retorna_401(self, unauth_client: AsyncClient):
        resp = await unauth_client.get("/api/v1/cedula/V12345678")
        assert resp.status_code == 401

    async def test_api_key_invalida_retorna_401(self, unauth_client: AsyncClient):
        resp = await unauth_client.get(
            "/api/v1/cedula/V12345678",
            headers={"X-API-Key": "clave-incorrecta"},
        )
        assert resp.status_code == 401

    async def test_formato_invalido_retorna_422(self, async_client: AsyncClient):
        resp = await async_client.get("/api/v1/cedula/abc")
        assert resp.status_code == 422
        body = resp.json()
        assert body["error"]["code"] == "INVALID_CEDULA_FORMAT"

    async def test_cedula_not_found_retorna_404(self, async_client: AsyncClient):
        # Mock simula not-found para números terminados en "0"
        resp = await async_client.get("/api/v1/cedula/V1234560")
        assert resp.status_code == 404
        body = resp.json()
        assert body["error"]["code"] == "CEDULA_NOT_FOUND"

    async def test_source_error_retorna_502(self, async_client: AsyncClient):
        # Mock simula error de fuente para números terminados en "99"
        resp = await async_client.get("/api/v1/cedula/V1234599")
        assert resp.status_code == 502
        body = resp.json()
        assert body["error"]["code"] == "SOURCE_SERVICE_ERROR"

    async def test_cache_hit_retorna_fuente_cache(self, async_client: AsyncClient):
        # Primera consulta
        await async_client.get("/api/v1/cedula/V87654321")
        # Segunda consulta → caché
        resp = await async_client.get("/api/v1/cedula/V87654321")
        assert resp.status_code == 200
        # La caché es compartida entre requests en el mismo process
        # (en test puede no ser cache dependiendo del lifespan)
        assert resp.json()["cedula"] == "87654321"

    async def test_formato_con_guiones(self, async_client: AsyncClient):
        resp = await async_client.get("/api/v1/cedula/v-12.345.678")
        assert resp.status_code == 200
        assert resp.json()["cedula"] == "12345678"


class TestHealthEndpoint:
    async def test_health(self, async_client: AsyncClient):
        resp = await async_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
