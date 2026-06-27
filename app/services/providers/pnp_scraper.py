"""Provider real: consulta sistemaspnp.com con flujo de dos pasos.

Flujo por cada consulta (cliente fresco = sesión PHP aislada):
  1. GET {SOURCE_URL}/  → obtiene PHPSESSID + parsea pregunta CAPTCHA aritmética
  2. Resuelve el CAPTCHA (suma simple: "¿Cuánto es X + Y?")
  3. POST {SOURCE_URL}/resultado.php con cedula, captcha (respuesta) y jeje="" (honeypot)
  4. Parsea el HTML de resultado: cards con <p><strong>Key:</strong> Valor</p>

Por qué cliente por consulta y no compartido:
  El sitio usa sesiones PHP (PHPSESSID). Un cliente compartido acumula cookies
  de sesiones anteriores, causando redirect loops. Crear un cliente nuevo por
  consulta garantiza cookie-jar vacío y sesión limpia.

Lanza excepciones de dominio (CedulaNotFoundError, SourceServiceError).
Si el HTML cambia, actualizar _parse_result() y/o _solve_captcha().
"""

import logging
import re

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.exceptions import CedulaNotFoundError, SourceServiceError
from app.models.cedula import Persona

logger = logging.getLogger(__name__)

_CAPTCHA_RE = re.compile(r"(\d+)\s*\+\s*(\d+)")


class PNPScraperProvider:
    """Provider que obtiene datos desde sistemaspnp.com."""

    name = "pnp"

    async def fetch(self, nacionalidad: str, numero: str) -> Persona:
        clave = f"{nacionalidad}{numero}"
        logger.info("Consultando fuente PNP para cédula %s", clave)

        base = settings.source_url.rstrip("/")
        index_url = base + "/"
        result_url = base + "/resultado.php"

        # Cliente fresco por consulta para aislar la sesión PHP
        async with httpx.AsyncClient(
            timeout=settings.request_timeout,
            headers={"User-Agent": settings.user_agent},
            follow_redirects=True,
        ) as client:
            # --- Paso 1: GET index → sesión + CAPTCHA ---
            try:
                r_index = await client.get(index_url)
                r_index.raise_for_status()
            except httpx.TimeoutException as exc:
                raise SourceServiceError("Timeout al obtener el formulario de consulta") from exc
            except httpx.RequestError as exc:
                raise SourceServiceError(f"Error de conexión con la fuente: {exc}") from exc

            captcha_answer = _solve_captcha(r_index.text)
            if captcha_answer is None:
                raise SourceServiceError("No se pudo resolver el CAPTCHA de la fuente")

            logger.debug("CAPTCHA resuelto: %d", captcha_answer)

            # --- Paso 2: POST resultado ---
            try:
                r_result = await client.post(
                    result_url,
                    data={
                        "cedula": numero,
                        "captcha": str(captcha_answer),
                        "jeje": "",  # honeypot — debe quedar vacío
                    },
                )
                r_result.raise_for_status()
            except httpx.TimeoutException as exc:
                raise SourceServiceError("Timeout al consultar los datos de la cédula") from exc
            except httpx.HTTPStatusError as exc:
                raise SourceServiceError(
                    f"La fuente respondió con HTTP {exc.response.status_code}"
                ) from exc
            except httpx.RequestError as exc:
                raise SourceServiceError(f"Error de conexión con la fuente: {exc}") from exc

        return _parse_result(r_result.text, clave, nacionalidad, numero)


def _solve_captcha(html: str) -> int | None:
    """Extrae y resuelve la operación aritmética del CAPTCHA.

    Busca el patrón 'X + Y' en el label de clase 'captcha-question'.
    Solo sumas de enteros positivos — la fuente usa exclusivamente este formato.
    """
    soup = BeautifulSoup(html, "lxml")
    label = soup.find("label", class_="captcha-question")
    if label is None:
        return None
    m = _CAPTCHA_RE.search(label.get_text())
    if m is None:
        return None
    return int(m.group(1)) + int(m.group(2))


def _parse_result(html: str, clave: str, nacionalidad: str, numero: str) -> Persona:
    """Parsea el HTML de resultado y construye una Persona.

    Estructura esperada:
      <div class='card'>
        <div class='card-body'>
          <p><strong>Primer Apellido:</strong> CUEVAS</p>
          <p><strong>Segundo Apellido:</strong> REGALADO</p>
          <p><strong>Nombres:</strong> JUAN ANDRES</p>
        </div>
      </div>

    Raises:
        CedulaNotFoundError: la cédula no existe en la fuente.
        SourceServiceError: sesión/CAPTCHA rechazado o HTML inesperado.
    """
    soup = BeautifulSoup(html, "lxml")

    # Detectar error de sesión/CAPTCHA (alert-danger)
    alert = soup.find("div", class_="alert-danger")
    if alert:
        alert_text = alert.get_text(strip=True)
        logger.warning("Alert de la fuente para %s: %s", clave, alert_text)
        if "sesi" in alert_text.lower() or "captcha" in alert_text.lower():
            raise SourceServiceError("CAPTCHA rechazado por la fuente — reintente la consulta")
        raise CedulaNotFoundError(clave)

    # Extraer campos: <p><strong>Key:</strong> Valor</p>
    fields: dict[str, str] = {}
    for p in soup.find_all("p"):
        strong = p.find("strong")
        if strong is None:
            continue
        key = strong.get_text(strip=True).rstrip(":")
        value = p.get_text(strip=True)[len(strong.get_text(strip=True)):].lstrip(":").strip()
        if key and value:
            fields[key] = value

    logger.debug("Campos extraídos para %s: %s", clave, fields)

    primer_apellido = fields.get("Primer Apellido", "")
    segundo_apellido = fields.get("Segundo Apellido", "")
    nombres = fields.get("Nombres", "")

    if not primer_apellido and not nombres:
        raise CedulaNotFoundError(clave)

    primer_nombre = nombres.split()[0] if nombres else ""
    partes = [p for p in [nombres, primer_apellido, segundo_apellido] if p]
    nombre_completo = " ".join(partes)

    return Persona(
        nacionalidad=nacionalidad,
        cedula=numero,
        nombre_completo=nombre_completo,
        primer_nombre=primer_nombre,
        primer_apellido=primer_apellido,
        segundo_apellido=segundo_apellido,
    )
