"""Interfaz (Protocol) del proveedor de datos de cédula."""

from typing import Protocol, runtime_checkable

from app.models.cedula import Persona


@runtime_checkable
class CedulaProvider(Protocol):
    name: str  # identificador del provider para el campo "fuente" en la respuesta

    async def fetch(self, nacionalidad: str, numero: str) -> Persona:
        """Obtiene la información de la persona dada su cédula.

        Args:
            nacionalidad: "V" o "E"
            numero: dígitos de la cédula sin prefijo

        Returns:
            Persona con los datos extraídos.

        Raises:
            CedulaNotFoundError: si la cédula no existe en la fuente.
            SourceServiceError: si la fuente falla o devuelve datos inesperados.
        """
        ...
