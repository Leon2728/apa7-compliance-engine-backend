from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from api.models.lint_models import LintRequest, LintResponse
from api.orchestrator.lint_orchestrator import LintOrchestrator
from api.rules_library import RuleLibrary
from api.routes import coach_router
from api.routes import extract_text_router
from api.routes import export_router
from api.config import get_settings
from api.security import api_key_auth
from api.exceptions import value_error_handler, general_exception_handler

# Obtener configuración
settings = get_settings()

# Configurar FastAPI con docs condicionales según entorno
app = FastAPI(
    title="APA7 Compliance Engine Backend",
    version="1.0.0",
    description="Motor de linting APA 7 + CUN basado en múltiples agentes.",
    # Desactivar docs en producción
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar manejadores de excepciones
app.add_exception_handler(ValueError, value_error_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Directorio base = carpeta api
BASE_DIR = Path(__file__).parent

# Cargamos la biblioteca de reglas desde api/rules/apa7_cun/*.rules.json
RULES_BASE_DIR = BASE_DIR / "rules"
rule_library = RuleLibrary(base_dir=RULES_BASE_DIR, profile_id="apa7_cun")

# Orquestador principal
orchestrator = LintOrchestrator(rule_library=rule_library)

# Registrar routers adicionales
app.include_router(coach_router.router)
app.include_router(extract_text_router.router)
app.include_router(export_router.export_router)


@app.get("/health")
async def health() -> dict:
    """
    Endpoint de salud básico.

    Devuelve:
      - estado
      - timestamp
      - entorno actual
      - lista de agentes para los que hay reglas cargadas
    """
    return {
        "status": "ok",
        "environment": settings.APA7_ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
        "rule_agents": rule_library.get_all_agent_ids(),
    }


@app.post("/lint", response_model=LintResponse, dependencies=[Depends(api_key_auth)])
async def lint(request: LintRequest) -> LintResponse:
    """
    Ejecuta el análisis APA7+CUN sobre el documento enviado.

    Requiere autenticación por API key (header X-API-Key) en producción.

    Espera:
      - LintRequest con document_text y context.
    Devuelve:
      - LintResponse con findings, summary, perfil y metadatos.
    """
    # Propagar metadata desde request a context si está presente
    if request.metadata and request.context.metadata is None:
        request.context.metadata = request.metadata

    return await orchestrator.run(request)
