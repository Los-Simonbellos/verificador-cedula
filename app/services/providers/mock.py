"""Provider mock/stub para desarrollo y tests.

No hace ninguna llamada de red. Devuelve datos deterministas basados
en el número de cédula para facilitar pruebas de distintos escenarios.

Números especiales:
  - Termina en "0"         → simula CedulaNotFoundError
  - Termina en "999...9"   → simula SourceServiceError
"""

from app.core.exceptions import CedulaNotFoundError, SourceServiceError
from app.models.cedula import Persona


class MockCedulaProvider:
    """Stub intercambiable con el provider real."""

    name = "mock"

    # Personas de ejemplo en la BD stub
    _DATABASE: dict[str, Persona] = {
        "V12345678": Persona(
            nacionalidad="V",
            cedula="12345678",
            nombre_completo="JUAN ANDRES CUEVAS RAMIREZ",
            primer_nombre="JUAN",
            primer_apellido="CUEVAS",
            segundo_apellido="RAMIREZ",
        ),
        "V87654321": Persona(
            nacionalidad="V",
            cedula="87654321",
            nombre_completo="MARIA GABRIELA LOPEZ SILVA",
            primer_nombre="MARIA",
            primer_apellido="LOPEZ",
            segundo_apellido="SILVA",
        ),
        "E11223344": Persona(
            nacionalidad="E",
            cedula="11223344",
            nombre_completo="CARLOS EDUARDO MARTINEZ PEREZ",
            primer_nombre="CARLOS",
            primer_apellido="MARTINEZ",
            segundo_apellido="PEREZ",
        ),
    }

    async def fetch(self, nacionalidad: str, numero: str) -> Persona:
        clave = f"{nacionalidad}{numero}"

        # Simulación de error en fuente (números que terminan en "99")
        if numero.endswith("99"):
            raise SourceServiceError(
                "Error simulado: la fuente no respondió (mock)"
            )

        # Simulación de not-found (números que terminan en "0")
        if numero.endswith("0"):
            raise CedulaNotFoundError(clave)

        # Buscar en BD stub
        if clave in self._DATABASE:
            return self._DATABASE[clave]

        # Generar persona genérica para cualquier otro número
        return Persona(
            nacionalidad=nacionalidad,
            cedula=numero,
            nombre_completo=f"PERSONA EJEMPLO {numero}",
            primer_nombre="PERSONA",
            primer_apellido="EJEMPLO",
        )
