"""Servicio central de consulta de cédula.

Responsabilidades:
  1. Validar y normalizar el número recibido.
  2. Consultar la caché (hit → responde directo).
  3. Delegar al provider (miss → fetch).
  4. Almacenar en caché.
  5. (Futuro) Registrar histórico si HISTORY_ENABLED.
  6. Construir y retornar PersonaResponse.

Regla de capa: no hay conceptos HTTP aquí (status codes, Request).
Las excepciones de dominio se propagan; los handlers de main.py las traducen.
"""

import logging
from datetime import datetime, timezone

from app.cache.base import CachePort
from app.core.config import settings
from app.models.cedula import Persona
from app.schemas.cedula import PersonaResponse
from app.services.providers.base import CedulaProvider
from app.utils.validators import normalize_cedula

logger = logging.getLogger(__name__)


class CedulaService:
    def __init__(self, provider: CedulaProvider, cache: CachePort) -> None:
        self._provider = provider
        self._cache = cache

    async def consultar(self, numero_raw: str) -> PersonaResponse:
        """Consulta la información de una cédula.

        Args:
            numero_raw: cédula en cualquier formato aceptado por normalize_cedula.

        Returns:
            PersonaResponse con los datos y metadata de la consulta.

        Raises:
            InvalidCedulaFormatError: formato inválido.
            CedulaNotFoundError: cédula no encontrada.
            SourceServiceError: error al contactar la fuente.
        """
        # 1. Normalizar y validar
        nacionalidad, numero = normalize_cedula(numero_raw)
        clave = f"{nacionalidad}{numero}"
        logger.debug("Consulta iniciada para clave %s", clave)

        # 2. Hit de caché
        cached: Persona | None = await self._cache.get(clave)
        if cached is not None:
            logger.info("Cache HIT para %s", clave)
            return self._build_response(cached, fuente="cache")

        # 3. Fetch del provider
        logger.info("Cache MISS para %s — consultando provider '%s'", clave, settings.provider)
        persona = await self._provider.fetch(nacionalidad, numero)

        # 4. Almacenar en caché
        await self._cache.set(clave, persona, settings.cache_ttl_seconds)
        logger.debug("Almacenado en caché: %s (TTL=%ds)", clave, settings.cache_ttl_seconds)

        # 5. Histórico (placeholder)
        if settings.history_enabled:
            await self._register_history(clave)

        # 6. Construir respuesta
        return self._build_response(persona, fuente=self._provider.name)

    @staticmethod
    def _build_response(persona: Persona, fuente: str) -> PersonaResponse:
        return PersonaResponse(
            nacionalidad=persona.nacionalidad,
            cedula=persona.cedula,
            nombre_completo=persona.nombre_completo,
            primer_nombre=persona.primer_nombre,
            primer_apellido=persona.primer_apellido,
            segundo_apellido=persona.segundo_apellido,
            consultado_en=datetime.now(timezone.utc),
            fuente=fuente,
        )

    async def _register_history(self, clave: str) -> None:
        """Placeholder: registrar consulta en PostgreSQL cuando esté habilitado."""
        # TODO: implementar con SQLAlchemy async + modelo ConsultaHistorica
        logger.debug("History stub: registraría consulta de %s", clave)
