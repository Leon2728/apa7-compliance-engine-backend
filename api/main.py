from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI

from api.models.lint_models import LintRequest, LintResponse
from api.orchestrator.lint_orchestrator import LintOrchestrator
from api.rules_library import RuleLibrary

app = FastAPI(
    title="APA7 Compliance Engine Backend",
    version="1.0.0",
    description="Motor de linting APA 7 + CUN basado en múltiples agentes.",
)

# Directorio base = carpeta api
BASE_DIR = Path(__file__).parent

# Cargamos la biblioteca de reglas desde api/rules/apa7_cun/*.rules.json
RULES_BASE_DIR = BASE_DIR / "rules"
rule_library = RuleLibrary(base_dir=RULES_BASE_DIR, profile_id="apa7_cun")

# Orquestador principal
orchestrator = LintOrchestrator(rule_library=rule_library)


@app.get("/health")
async def health() -> dict:
    """
    Endpoint de salud básico.

    Devuelve:
      - estado
      - timestamp
      - lista de agentes para los que hay reglas cargadas
    """
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "rule_agents": rule_library.get_all_agent_ids(),
    }


@app.post("/lint", response_model=LintResponse)
async def lint(request: LintRequest) -> LintResponse:
    """
    Ejecuta el análisis APA7+CUN sobre el documento enviado.

    Espera:
      - LintRequest con document_text y context.
    Devuelve:
      - LintResponse con findings, summary, perfil y metadatos.
    """
    return await orchestrator.run(request)
