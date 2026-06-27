# Verificador de Cédula Venezolana

Servicio REST en FastAPI que consulta la información básica de una persona dado su número de cédula de identidad venezolana.

## ⚠️ Advertencia legal / PII

Este servicio accede y expone **datos de carácter personal** (nombre completo de personas físicas). Antes de desplegarlo:

- Verifica el cumplimiento de la **Ley de Infogobierno** y normativas venezolanas de protección de datos.
- Respeta el `robots.txt` y los **términos de servicio** de la fuente (`sistemaspnp.com`).
- Implementa controles de acceso y auditoría para limitar quién puede consultar datos.
- No almacenes PII sin una justificación legal clara y mecanismos de retención/eliminación.

---

## Estructura del repositorio

Cada archivo está marcado según dónde vive y para qué sirve:

```
verificador-cedula/
│
│  ── DESPLIEGUE EN VERCEL ─────────────────────────────────────────
│
├── api/
│   └── index.py          [VERCEL] Entry point: expone `app` al runtime
│
├── app/                  [VERCEL] Código de la aplicación (se incluye en el bundle)
│   ├── main.py                    App factory + lifespan
│   ├── core/
│   │   ├── config.py              Settings via pydantic-settings (lee env vars)
│   │   ├── exceptions.py          Excepciones de dominio + handlers HTTP
│   │   ├── security.py            Autenticación API Key (X-API-Key)
│   │   └── logging.py
│   ├── routers/
│   │   ├── cedula.py              GET /api/v1/cedula/{numero}
│   │   └── health.py              GET /health
│   ├── schemas/
│   │   └── cedula.py              PersonaResponse, HealthResponse (Pydantic v2)
│   ├── models/
│   │   └── cedula.py              Dataclass Persona (dominio puro)
│   ├── services/
│   │   ├── cedula_service.py      Orquestación: validar → caché → provider
│   │   └── providers/
│   │       ├── base.py            Protocol CedulaProvider
│   │       ├── mock.py            Stub para desarrollo (PROVIDER=mock)
│   │       └── pnp_scraper.py     Scraper real sistemaspnp.com (PROVIDER=pnp)
│   ├── cache/
│   │   ├── base.py                Protocol CachePort
│   │   └── memory.py              InMemoryTTLCache (stateless en Vercel)
│   └── utils/
│       └── validators.py          normalize_cedula()
│
├── requirements.txt      [VERCEL BUILD] pip instala estas deps durante el build
├── vercel.json           [VERCEL BUILD] Configura runtime, rutas y timeout
│
│  ── SOLO DESARROLLO LOCAL ────────────────────────────────────────
│
├── tests/                [LOCAL] Suite de pruebas (pytest)
│   ├── conftest.py                Fixtures: AsyncClient + dependency overrides
│   ├── test_validators.py         Tests unitarios del validador de cédulas
│   ├── test_service.py            Tests del servicio (caché hit/miss, errores)
│   └── test_cedula_router.py      Tests de integración del router HTTP
│
├── pyproject.toml        [LOCAL] Metadata + deps para uv + config de ruff/pytest
├── uv.lock               [LOCAL] Lockfile reproducible de uv
├── justfile              [LOCAL] Comandos del task runner (just)
├── .env.example          [LOCAL] Plantilla de variables de entorno
├── .env                  [LOCAL/GITIGNORED] Variables de entorno reales
└── .gitignore
```

### Resumen: ¿qué va a Vercel y qué no?

| Archivo / Carpeta | Va a Vercel | Motivo |
|---|:---:|---|
| `api/index.py` | ✅ bundle | Entry point que el runtime necesita |
| `app/` | ✅ bundle | Toda la lógica de la aplicación |
| `requirements.txt` | ✅ build | Vercel usa `pip` para instalar deps |
| `vercel.json` | ✅ build | Configura el build, no va en el bundle |
| `tests/` | ❌ | Solo se ejecutan en CI/local |
| `pyproject.toml` | ❌ | Usado por `uv` localmente |
| `uv.lock` | ❌ | Lockfile de `uv`, no de `pip` |
| `justfile` | ❌ | Task runner solo disponible en local |
| `.env` | ❌ gitignored | Las vars van en el dashboard de Vercel |
| `.env.example` | ❌ | Referencia documental, no se usa en prod |

> **Por qué dos archivos de dependencias (`pyproject.toml` y `requirements.txt`)**
>
> `uv` (gestor local) lee `pyproject.toml` y genera `uv.lock` para reproducibilidad en desarrollo.
> Vercel usa `pip` con `requirements.txt` durante el build — son las mismas dependencias runtime,
> declaradas en el formato que cada herramienta entiende.

---

## Despliegue en Vercel

### Variables de entorno (configurar en el dashboard de Vercel)

| Variable | Ejemplo | Descripción |
|---|---|---|
| `API_KEY` | `una-clave-secreta` | Clave de autenticación del servicio |
| `PROVIDER` | `pnp` | `pnp` = scraper real · `mock` = stub sin red |
| `SOURCE_URL` | `https://www.sistemaspnp.com/cedula` | URL base de la fuente |
| `REQUEST_TIMEOUT` | `8` | Timeout HTTP en segundos (máx. 8 en Hobby) |
| `CACHE_TTL_SECONDS` | `3600` | TTL del caché en segundos |
| `LOG_LEVEL` | `INFO` | Nivel de logging |

> **No configurar `HTTP_TIMEOUT`** — es una variable interna de `uv` y causará errores en el build.

### Comportamiento del caché en Vercel (serverless)

En Vercel cada invocación es una función serverless. El `InMemoryTTLCache` funciona así:

- **Función caliente** (invocaciones consecutivas): el caché persiste en memoria → sin requests redundantes a la fuente.
- **Cold start**: la instancia es nueva → el caché arranca vacío → primer request siempre va a la fuente.

Para caché persistente entre instancias, la siguiente iteración es **Upstash Redis** (ver sección "Próximos pasos").

### Desplegar

```bash
# Instalar Vercel CLI
npm i -g vercel

# Primera vez: vincular proyecto
vercel

# Producción
vercel --prod

# O con just:
just deploy       # preview
just deploy-prod  # producción
```

---

## Desarrollo local

### Prerrequisitos

- Python 3.12+ (recomendado 3.14 para coincidir con el entorno local configurado)
- [uv](https://docs.astral.sh/uv/) — gestor de paquetes
- [just](https://just.systems/) — task runner

### Setup

```bash
# 1. Instalar dependencias (runtime + dev)
just install

# 2. Configurar entorno
cp .env.example .env
# Editar .env: cambiar API_KEY y elegir PROVIDER (mock o pnp)

# 3. Arrancar servidor (PROVIDER=mock por defecto — sin red)
just run
```

El servidor arranca en `http://localhost:8000`.

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Comandos disponibles

```bash
just install      # instalar deps con uv
just run          # servidor de desarrollo (mock)
just run-pnp      # servidor con scraper real
just test         # ejecutar tests
just test-cov     # tests con cobertura
just lint         # ruff check
just fmt          # ruff format
just deploy       # deploy a Vercel (preview)
just deploy-prod  # deploy a Vercel (producción)
```

---

## Uso de la API

### Consultar una cédula

```bash
curl -s -H "X-API-Key: <tu-api-key>" \
  http://localhost:8000/api/v1/cedula/V12345678 | python3 -m json.tool
```

**Respuesta 200:**

```json
{
  "nacionalidad": "V",
  "cedula": "12345678",
  "nombre_completo": "JUAN ANDRES CUEVAS REGALADO",
  "primer_nombre": "JUAN",
  "primer_apellido": "CUEVAS",
  "segundo_apellido": "REGALADO",
  "consultado_en": "2026-06-27T12:00:00Z",
  "fuente": "pnp"
}
```

El campo `fuente` indica el origen del dato:

| Valor | Significa |
|---|---|
| `pnp` | Dato fresco desde sistemaspnp.com |
| `mock` | Stub de desarrollo (sin red) |
| `cache` | Resultado servido desde caché |

**Formatos de cédula aceptados:**

| Entrada | Interpretado como |
|---|---|
| `V12345678` | Venezolano, número 12345678 |
| `E11223344` | Extranjero, número 11223344 |
| `v-12.345.678` | Normalizado → V12345678 |
| `12345678` | Sin prefijo → asume venezolano |

### Códigos de error

| HTTP | Código en body | Causa |
|---|---|---|
| 401 | — | `X-API-Key` ausente o inválida |
| 404 | `CEDULA_NOT_FOUND` | Cédula no encontrada en la fuente |
| 422 | `INVALID_CEDULA_FORMAT` | Formato de cédula inválido |
| 502 | `SOURCE_SERVICE_ERROR` | Fallo al contactar o parsear la fuente |

### Health check

```bash
curl http://localhost:8000/health
# {"status":"ok","version":"0.1.0"}
```

---

## Tests

Los tests usan `MockCedulaProvider` y no hacen llamadas de red. El fixture de `conftest.py` inyecta el servicio vía `app.dependency_overrides` para evitar depender del lifespan de FastAPI.

```bash
just test       # 30 tests
just test-cov   # con reporte de cobertura
```

**Números especiales del mock:**

| Cédula | Comportamiento |
|---|---|
| Termina en `0` (ej. `V1234560`) | Simula `CedulaNotFoundError` → 404 |
| Termina en `99` (ej. `V1234599`) | Simula `SourceServiceError` → 502 |
| Cualquier otro | Devuelve persona genérica o de la BD stub |

---

## Arquitectura

```
Request HTTP
     │
     ▼
 Router (app/routers/)          ← HTTP puro: validación, auth, DI
     │
     ▼
 CedulaService                  ← Lógica: validar → caché → provider
     │
     ├── CachePort ──────────── InMemoryTTLCache (o RedisCache en futuro)
     │
     └── CedulaProvider ──────── MockCedulaProvider (PROVIDER=mock)
                                 PNPScraperProvider  (PROVIDER=pnp)
                                   │
                                   └── GET sistemaspnp.com/cedula/ (CAPTCHA)
                                       POST resultado.php (datos)
```

---

## Próximos pasos

### Caché persistente con Upstash Redis

1. `uv add redis[asyncio]`
2. Crear `app/cache/redis_cache.py` implementando `CachePort` (3 métodos: `get`, `set`, `delete`).
3. En `main.py`, instanciar `RedisCache` si `settings.redis_url` está presente.
4. Añadir `REDIS_URL` como variable de entorno en Vercel (Upstash tiene integración nativa).

### Histórico de consultas con PostgreSQL + Alembic

1. `uv add sqlalchemy[asyncio] asyncpg alembic`
2. Crear modelo `ConsultaHistorica` en `app/models/`.
3. `alembic init migrations` y configurar `env.py` con `DATABASE_URL`.
4. Implementar `_register_history()` en `CedulaService`.
5. Activar con `HISTORY_ENABLED=true` en el dashboard de Vercel.

### Rate limiting

- `uv add slowapi` e integrar el middleware en `main.py`.
- Con Redis ya disponible, el contador de requests puede almacenarse ahí.
