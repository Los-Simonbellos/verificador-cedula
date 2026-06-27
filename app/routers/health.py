"""Endpoint de health check."""

from fastapi import APIRouter

from app.schemas.cedula import HealthResponse

router = APIRouter(tags=["infra"])


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health() -> HealthResponse:
    """Verifica que el servicio está activo."""
    return HealthResponse()
