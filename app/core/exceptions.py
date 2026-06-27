from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# ---------------------------------------------------------------------------
# Domain exceptions (no HTTP concepts here)
# ---------------------------------------------------------------------------


class InvalidCedulaFormatError(Exception):
    """La cédula proporcionada tiene un formato inválido."""

    def __init__(self, cedula: str, detail: str = "Formato inválido") -> None:
        self.cedula = cedula
        self.detail = detail
        super().__init__(f"Cédula inválida '{cedula}': {detail}")


class CedulaNotFoundError(Exception):
    """No se encontró información para la cédula consultada."""

    def __init__(self, cedula: str) -> None:
        self.cedula = cedula
        super().__init__(f"No se encontró información para la cédula '{cedula}'")


class SourceServiceError(Exception):
    """Error al contactar o parsear la fuente externa de datos."""

    def __init__(self, detail: str = "Error en el servicio de origen") -> None:
        self.detail = detail
        super().__init__(detail)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

_ERROR_BODY = "error"


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={_ERROR_BODY: {"code": code, "message": message}},
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(InvalidCedulaFormatError)
    async def handle_invalid_format(
        request: Request, exc: InvalidCedulaFormatError
    ) -> JSONResponse:
        return _error_response(422, "INVALID_CEDULA_FORMAT", exc.detail)

    @app.exception_handler(CedulaNotFoundError)
    async def handle_not_found(
        request: Request, exc: CedulaNotFoundError
    ) -> JSONResponse:
        return _error_response(
            404,
            "CEDULA_NOT_FOUND",
            f"No se encontró información para la cédula '{exc.cedula}'",
        )

    @app.exception_handler(SourceServiceError)
    async def handle_source_error(
        request: Request, exc: SourceServiceError
    ) -> JSONResponse:
        return _error_response(502, "SOURCE_SERVICE_ERROR", exc.detail)
