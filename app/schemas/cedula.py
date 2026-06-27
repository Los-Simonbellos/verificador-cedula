from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


class PersonaResponse(BaseModel):
    """Respuesta pública de una consulta de cédula."""

    model_config = ConfigDict(from_attributes=True)

    nacionalidad: str = Field(..., examples=["V"], description="'V' venezolano, 'E' extranjero")
    cedula: str = Field(..., examples=["12345678"], description="Número sin prefijo")
    nombre_completo: str = Field(..., examples=["JUAN ANDRES CUEVAS"])
    primer_nombre: str = Field(..., examples=["JUAN"])
    primer_apellido: str = Field(..., examples=["CUEVAS"])
    segundo_apellido: str = Field("", examples=["REGALADO"])
    consultado_en: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp UTC de la consulta",
    )
    fuente: str = Field(
        ...,
        examples=["mock", "pnp", "cache"],
        description="Origen del dato: 'pnp' fuente real, 'mock' stub, 'cache' resultado cacheado",
    )


class HealthResponse(BaseModel):
    """Respuesta del endpoint de salud."""

    status: str = "ok"
    version: str = "0.1.0"
