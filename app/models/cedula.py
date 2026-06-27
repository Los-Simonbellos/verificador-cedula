"""Modelo de dominio para la información de una persona.

Intencionalidad: esta es una clase de datos pura, sin lógica de negocio
ni dependencias de ORM o Pydantic. Cuando se active HISTORY_ENABLED,
se añadirá un modelo SQLAlchemy en este mismo módulo o en uno adyacente.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Persona:
    """Información básica de una persona extraída de la fuente de datos."""

    nacionalidad: str       # "V" o "E"
    cedula: str             # solo dígitos, ej. "12345678"
    nombre_completo: str    # "JUAN ANDRES CUEVAS REGALADO"
    primer_nombre: str
    primer_apellido: str
    segundo_apellido: str = ""

    @property
    def clave(self) -> str:
        """Clave única para la caché: ej. 'V12345678'."""
        return f"{self.nacionalidad}{self.cedula}"
