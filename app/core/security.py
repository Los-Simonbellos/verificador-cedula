import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: Annotated[str | None, Security(_api_key_header)],
) -> None:
    """Dependencia que valida el header X-API-Key contra settings.api_key."""
    if not api_key or not secrets.compare_digest(api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida o ausente",
            headers={"WWW-Authenticate": "ApiKey"},
        )


# Typed alias para inyectar en routers con Depends
ApiKeyDep = Annotated[None, Depends(verify_api_key)]
