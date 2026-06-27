"""Interfaz (Protocol) del puerto de caché.

Cualquier implementación (in-memory, Redis, Memcached) debe respetar
este contrato para ser intercambiable sin modificar el service.
"""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class CachePort(Protocol):
    async def get(self, key: str) -> Any | None:
        """Retorna el valor cacheado o None si no existe / expiró."""
        ...

    async def set(self, key: str, value: Any, ttl: int) -> None:
        """Almacena `value` bajo `key` con TTL en segundos."""
        ...

    async def delete(self, key: str) -> None:
        """Elimina la entrada de caché (útil para invalidación manual)."""
        ...
