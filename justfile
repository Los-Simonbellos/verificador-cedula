# -----------------------------------------------
# verificador-cedula — Justfile
# Requiere: just, uv
# -----------------------------------------------

# Mostrar tareas disponibles
default:
    @just --list

# Instalar dependencias (runtime + dev)
install:
    uv sync --group dev

# Arrancar servidor de desarrollo
run:
    uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Arrancar con provider real (pnp) — requiere .env con API_KEY real
run-pnp:
    PROVIDER=pnp uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Ejecutar tests
test:
    uv run pytest -v

# Ejecutar tests con cobertura
test-cov:
    uv run pytest --cov=app --cov-report=term-missing -v

# Linting con ruff
lint:
    uv run ruff check app/ tests/

# Formateo automático
fmt:
    uv run ruff format app/ tests/

# Lint + format en un solo paso (CI)
check:
    uv run ruff check app/ tests/
    uv run ruff format --check app/ tests/

# Ejemplo de curl con mock (dev)
curl-example:
    curl -s -H "X-API-Key: changeme" http://localhost:8000/api/v1/cedula/V12345678 | python3 -m json.tool
