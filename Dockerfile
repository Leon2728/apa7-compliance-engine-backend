# Etapa de construcción optimizada para FastAPI backend APA7
FROM python:3.11-slim as production

# Establecer directorio de trabajo
WORKDIR /app

# Variables de entorno por defecto (serán sobrescritas en runtime)
ENV APA7_ENVIRONMENT=prod \
    APA7_API_KEYS="" \
    APA7_CORS_ORIGINS='["*"]' \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Instalar dependencias del sistema (mínimas)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements.txt
COPY requirements.txt .

# Instalar dependencias Python en modo producción (sin dev-tools)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip uninstall -y pytest pytest-cov black flake8 pylint mypy python-docx

# Copiar código de la aplicación
COPY api/ ./api/
COPY docs/ ./docs/

# Crear usuario no-root para seguridad
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Comando para arrancar el servidor
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
