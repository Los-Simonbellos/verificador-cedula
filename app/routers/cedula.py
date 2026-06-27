"""Router de consulta de cédula.

Capa HTTP pura: routing, validación de entrada vía FastAPI/Pydantic,
inyección de dependencias. Sin lógica de negocio ni queries de DB.

Las excepciones de dominio (InvalidCedulaFormatError, CedulaNotFoundError,
SourceServiceError) son manejadas por los handlers globales registrados en main.py.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.core.security import ApiKeyDep
from app.schemas.cedula import PersonaResponse
from app.services.cedula_service import CedulaService
from app.services.providers import get_provider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cedula", tags=["cédula"])


# ---------------------------------------------------------------------------
# Dependency factories
# ---------------------------------------------------------------------------


def get_cedula_service(request: Request) -> CedulaService:
    """Construye el CedulaService con el provider configurado y la caché del lifespan."""
    cache = request.app.state.cache
    return CedulaService(provider=get_provider(), cache=cache)


CedulaServiceDep = Annotated[CedulaService, Depends(get_cedula_service)]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/{numero}",
    response_model=PersonaResponse,
    summary="Consultar información por cédula",
    responses={
        200: {"description": "Información de la persona encontrada"},
        401: {"description": "API Key inválida o ausente"},
        404: {"description": "Cédula no encontrada en la fuente"},
        422: {"description": "Formato de cédula inválido"},
        502: {"description": "Error al consultar la fuente externa"},
    },
)
async def consultar_cedula(
    numero: str,
    _: ApiKeyDep,
    service: CedulaServiceDep,
) -> PersonaResponse:
    """Consulta la información básica de una persona dado su número de cédula venezolana.

    **Formatos aceptados:**
    - `V12345678` o `E12345678` (con prefijo de nacionalidad)
    - `v-12.345.678` (normalizado automáticamente)
    - `12345678` (sin prefijo → asume venezolano)

    **Fuente del dato** se indica en el campo `fuente`:
    - `pnp`: dato fresco desde la fuente original
    - `mock`: dato de stub (modo desarrollo)
    - `cache`: resultado previamente almacenado en caché
    """
    logger.info("GET /cedula/%s", numero)
    return await service.consultar(numero)
