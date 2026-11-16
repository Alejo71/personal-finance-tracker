
FROM python:3.12-slim

# Instalar uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY pyproject.toml uv.lock ./

# Instalar dependencias sin instalar el proyecto
RUN uv sync --frozen --no-install-project

# Copiar backend
COPY backend/app ./backend/app

# Activar entorno virtual
ENV PATH="/app/.venv/bin:$PATH"

# Ejecutar aplicación
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
