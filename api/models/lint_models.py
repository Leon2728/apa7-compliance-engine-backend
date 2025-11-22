from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict

from api.rules_models import Severity  # reutilizamos el enum de reglas
from api.models.layout_models import DocumentLayout


class LintContext(BaseModel):
    """
    Contexto que envía el cliente sobre el documento.
    Sirve para ajustar perfil, idioma, institución, etc.
    """

    model_config = ConfigDict(extra="ignore")

    document_type: Optional[str] = Field(
        default=None,
        description="Tipo declarado por el usuario (ensayo, informe de investigación, etc.)",
    )
    style: str = Field(default="APA7", description="Estilo de citación objetivo")
    institution: str = Field(default="CUN", description="Institución objetivo")
    language: Literal["es", "en"] = Field(
        default="es", description="Idioma predominante declarado"
    )
    profile_id: str = Field(
        default="apa7_cun",
        description="Perfil de reglas a usar (ej: 'apa7_cun')",
            layout: Optional[DocumentLayout] = None
    )


class DocumentProfile(BaseModel):
    """
    Perfil inferido del documento tras análisis básico
    (tipo, idioma, institución, etc.).
    """

    model_config = ConfigDict(extra="ignore")

    inferred_type: Optional[str] = None
    language: Optional[str] = None
    style: Optional[str] = None
    institution: Optional[str] = None
    confidence: float = 0.0
    raw_tags: List[str] = []


class FindingLocation(BaseModel):
    """Ubicación aproximada de un hallazgo en el documento."""

    model_config = ConfigDict(extra="ignore")

    line: Optional[int] = None
    column: Optional[int] = None
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None
    section: Optional[str] = None


class Finding(BaseModel):
    """
    Hallazgo APA: algo que el documento cumple o incumple
    según un agente + regla.
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    agent_id: str
    rule_id: Optional[str] = None
    severity: Severity
    category: str
    message: str
    suggestion: Optional[str] = None
    details: Optional[str] = None
    location: Optional[FindingLocation] = None
    snippet: Optional[str] = None


class LintSummary(BaseModel):
    """Resumen numérico de los hallazgos."""

    model_config = ConfigDict(extra="ignore")

    error_count: int
    warning_count: int
    suggestion_count: int


class LintRequest(BaseModel):
    """
    Payload de entrada para POST /lint.
    """

    model_config = ConfigDict(extra="ignore")

    document_text: str = Field(..., description="Texto completo del documento")
    context: LintContext = Field(
        default_factory=LintContext, description="Contexto opcional de linting"
    )


class LintResponse(BaseModel):
    """
    Respuesta estándar del motor de linting.
    """

    model_config = ConfigDict(extra="ignore")

    success: bool
    findings: List[Finding]
    summary: LintSummary
    agents_run: List[str]
    elapsed_ms: float
    profile: DocumentProfile
    timestamp: datetime
