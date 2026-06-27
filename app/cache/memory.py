"""Implementación en memoria con TTL.

Thread-safe para single-process. Para múltiples workers usar Redis.
"""

import asyncio
import time
from typing import Any


class InMemoryTTLCache:
    """Caché en memoria basada en dict con expiración por timestamp.

    Compatible con el protocolo CachePort.
    """

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float]] = {}  # key → (value, expire_at)
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expire_at = entry
            if time.monotonic() > expire_at:
                del self._store[key]
                return None
            return value

    async def set(self, key: str, value: Any, ttl: int) -> None:
        async with self._lock:
            expire_at = time.monotonic() + ttl
            self._store[key] = (value, expire_at)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)

    def size(self) -> int:
        """Número de entradas activas (sin contar expiradas)."""
        now = time.monotonic()
        return sum(1 for _, exp in self._store.values() if now <= exp)
