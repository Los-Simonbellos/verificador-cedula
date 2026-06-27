"""Validación y normalización de cédulas de identidad venezolanas.

Formatos aceptados:
  - "V12345678"   → ("V", "12345678")
  - "E12345678"   → ("E", "12345678")  # extranjero
  - "v-12.345.678"→ normaliza a ("V", "12345678")
  - "12345678"    → asume Venezuela → ("V", "12345678")

Restricciones:
  - 6 a 9 dígitos
  - Solo nacionalidad V o E
"""

import re

from app.core.exceptions import InvalidCedulaFormatError

# Mínimo y máximo de dígitos históricos del registro civil venezolano
_MIN_DIGITS = 6
_MAX_DIGITS = 9
_VALID_NATIONALITIES = {"V", "E"}

_STRIP_PATTERN = re.compile(r"[.\-\s]")


def normalize_cedula(raw: str) -> tuple[str, str]:
    """Normaliza y valida una cédula venezolana.

    Returns:
        Tupla (nacionalidad, numero) — ej. ("V", "12345678").

    Raises:
        InvalidCedulaFormatError: si el formato es inválido.
    """
    if not raw or not isinstance(raw, str):
        raise InvalidCedulaFormatError(str(raw), "El valor no puede estar vacío")

    cleaned = _STRIP_PATTERN.sub("", raw.strip().upper())

    # Extraer prefijo de nacionalidad
    if cleaned and cleaned[0] in _VALID_NATIONALITIES:
        nacionalidad = cleaned[0]
        numero = cleaned[1:]
    elif cleaned.isdigit():
        # Sin prefijo → asumir venezolano
        nacionalidad = "V"
        numero = cleaned
    else:
        raise InvalidCedulaFormatError(
            raw,
            f"Prefijo '{cleaned[0]}' inválido. Use V (venezolano) o E (extranjero)",
        )

    # Validar que el número sea sólo dígitos
    if not numero.isdigit():
        raise InvalidCedulaFormatError(raw, "El número de cédula debe contener solo dígitos")

    # Validar longitud
    if not (_MIN_DIGITS <= len(numero) <= _MAX_DIGITS):
        raise InvalidCedulaFormatError(
            raw,
            f"La cédula debe tener entre {_MIN_DIGITS} y {_MAX_DIGITS} dígitos "
            f"(se recibieron {len(numero)})",
        )

    return nacionalidad, numero
