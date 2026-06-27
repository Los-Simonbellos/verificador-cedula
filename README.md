# Verificador de Cédula Venezolana

Servicio REST en FastAPI que consulta la información básica de una persona dado su número de cédula de identidad venezolana.

## ⚠️ Advertencia legal / PII

Este servicio accede y expone **datos de carácter personal** (nombre completo de personas físicas). Antes de desplegarlo:

- Verifica el cumplimiento de la **Ley de Infogobierno** y normativas venezolanas de protección de datos.
- Respeta el `robots.txt` y los **términos de servicio** de la fuente (`sistemaspnp.com`).
- Implementa controles de acceso y auditoría para limitar quién puede consultar datos.
- No almacenes PII sin una justificación legal clara y mecanismos de retención/eliminación.

---

## Stack

| Componente | Tecnología |
|---|---|
| Framework | FastAPI + Uvicorn |
| Validación | Pydantic v2 |
| HTTP client | httpx (async) |
| HTML parsing | BeautifulSoup4 + lxml |
| Caché | In-memory TTL (Redis en próxima iteración) |
| Gestor de paquetes | uv |
| Task runner | just |

---

## Inicio rápido

### 1. Prerrequisitos

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- [just](https://just.systems/)

### 2. Instalar dependencias

```bash
just install
```

### 3. Configurar entorno

```bash
cp .env.example .env
# Edita .env y pon una API_KEY segura
```

### 4. Arrancar el servidor (modo mock, sin llamadas de red)

```bash
just run
```

El servidor arranca en `http://localhost:8000`.

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Uso

### Consultar una cédula

```bash
curl -s -H "X-API-Key: changeme" \
  http://localhost:8000/api/v1/cedula/V12345678 | python3 -m json.tool
```

**Respuesta 200:**

```json
{
  "nacionalidad": "V",
  "cedula": "12345678",
  "nombre_completo": "JUAN ANDRES CUEVAS RAMIREZ",
  "primer_nombre": "JUAN",
  "primer_apellido": "CUEVAS",
  "consultado_en": "2026-06-27T12:00:00Z",
  "fuente": "mock"
}
```

**Formatos de cédula aceptados:**

| Entrada | Resultado |
|---|---|
| `V12345678` | venezolano |
| `E11223344` | extranjero |
| `v-12.345.678` | normalizado |
| `12345678` | asume V |

### Cambiar al provider real (scraper)

```bash
# En .env:
PROVIDER=pnp

# O en una sesión puntual:
PROVIDER=pnp just run
```

### Health check

```bash
curl http://localhost:8000/health
```

---

## Códigos de error

| HTTP | Código | Causa |
|---|---|---|
| 401 | — | API Key ausente o inválida |
| 404 | `CEDULA_NOT_FOUND` | Cédula no encontrada en la fuente |
| 422 | `INVALID_CEDULA_FORMAT` | Formato de cédula inválido |
| 502 | `SOURCE_SERVICE_ERROR` | Fallo al contactar/parsear la fuente |

---

## Tests

```bash
just test           # todos los tests
just test-cov       # con cobertura
```

---

## Estructura del proyecto

```
app/
├── core/           # config, seguridad, excepciones, logging
├── routers/        # capa HTTP (routing + DI)
├── schemas/        # Pydantic v2 (request/response)
├── models/         # dataclasses de dominio
├── services/
│   ├── cedula_service.py      # orquestación
│   └── providers/             # fuentes de datos intercambiables
│       ├── base.py            # Protocol
│       ├── mock.py            # stub de desarrollo
│       └── pnp_scraper.py     # scraper real
├── cache/
│   ├── base.py    # CachePort (Protocol)
│   └── memory.py  # InMemoryTTLCache
└── utils/
    └── validators.py  # normalize_cedula()
```

---

## Próximos pasos

### Activar Redis como caché

1. Añadir dependencia: `uv add redis[asyncio]`
2. Crear `app/cache/redis_cache.py` implementando `CachePort`.
3. En `main.py`, reemplazar `InMemoryTTLCache()` por `RedisCache(url=settings.redis_url)` según `settings.cache_backend`.

### Activar PostgreSQL + Alembic (histórico)

1. `uv add sqlalchemy[asyncio] asyncpg alembic`
2. Crear modelo `ConsultaHistorica` en `app/models/`.
3. `alembic init migrations` y configurar `env.py`.
4. Implementar `_register_history()` en `CedulaService`.
5. Activar con `HISTORY_ENABLED=true` en `.env`.

### Rate limiting

- Añadir `slowapi` o implementar middleware con contador en Redis.
