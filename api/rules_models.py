from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class Severity(str, Enum):
    """Nivel de severidad de una regla/hallazgo."""

    error = "error"
    warning = "warning"
    suggestion = "suggestion"


class CheckType(str, Enum):
    """Tipo de chequeo que requiere la regla."""

    regex = "regex"
    structural = "structural"
    semantic = "semantic"
        llm_semantic = "llm_semantic"


class DetectionScope(str, Enum):
    """Ámbito de aplicación de la detección."""

    document = "document"
    section = "section"
    line = "line"
    block = "block"


class RuleSource(str, Enum):
    """Origen normativo principal de la regla."""

    APA7 = "APA7"
    LOCAL = "LOCAL"
    MIXED = "MIXED"


class RuleExamples(BaseModel):
    """Ejemplos de aplicación correcta e incorrecta de la regla."""

    model_config = ConfigDict(extra="ignore")

    good: str
    bad: str


class RuleDetectionHints(BaseModel):
    """
    Pistas para el motor sobre cómo detectar esta regla en el texto.

    Coincide con la estructura esperada en los .rules.json:

      "detectionHints": {
        "scope": "document" | "section" | "line" | "block",
        "sectionTargets": ["..."],
        "regex": ["..."],
        "notes": "..."
      }
    """

    model_config = ConfigDict(extra="ignore")

    scope: DetectionScope
    section_targets: Optional[List[str]] = Field(
        default=None,
        alias="sectionTargets",
        description="Nombres de secciones objetivo (ej: 'RESUMEN', 'REFERENCIAS').",
    )
    regex: Optional[List[str]] = Field(
        default=None,
        description="Lista de patrones regex que ayudan a localizar la condición.",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Notas adicionales para el desarrollador o el motor.",
    )

class LLMCheckMode(str, Enum):
    """Modo de evaluación del LLM en una regla."""
    validator = "validator"
    classifier = "classifier"
    suggester = "suggester"
    generator = "generator"

class LLMRuleConfig(BaseModel):
    """Configuración de LLM para una regla con checkType='llm_semantic'."""
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    
    enabled: bool = Field(
        default=True,
        description="Habilita o deshabilita la evaluación LLM para esta regla."
    )
    mode: LLMCheckMode = Field(
        default=LLMCheckMode.validator,
        description="Modo de evaluación del LLM."
    )
    prompt_template_id: Optional[str] = Field(
        default=None,
        alias="promptTemplateId",
        description="ID del template de prompt personalizado."
    )
    max_chars: int = Field(
        default=4000,
        description="Máximo número de caracteres del documento a enviar al LLM."
    )
    forbidden_behaviors: List[str] = Field(
        default_factory=list,
        description="Lista de comportamientos prohibidos que el LLM debe evitar."
    )
    allowed_suggestion_types: List[str] = Field(
        default_factory=list,
        description="Tipos de sugerencias permitidas del LLM."
    )
    output_format: str = Field(
        default="JSON_FINDINGS_V1",
        description="Formato esperado de la salida del LLM."
    )


class Rule(BaseModel):
    """
    Representa una regla individual de la biblioteca.

    Compatible 1:1 con los JSON del backend TypeScript:

      {
        "ruleId": "CUN-REF-001",
        "title": "...",
        "description": "...",
        "source": "APA7" | "LOCAL" | "MIXED",
        "baseStandard": "APA7",
        "apaReference": "APA 7, secc. ...",
        "localReference": "Manual APA CUN, ...",
        "severity": "error" | "warning" | "suggestion",
        "checkType": "regex" | "structural" | "semantic",
        "examples": { "good": "...", "bad": "..." },
        "detectionHints": { ... },
        "autoFixHint": "..."
      }
    """

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )

    rule_id: str = Field(
        alias="ruleId",
        description="Identificador único de la regla (ej: 'CUN-REF-001').",
    )
    title: str = Field(
        description="Título corto y descriptivo de la regla.",
    )
    description: str = Field(
        description="Descripción textual de la norma que se está validando.",
    )

    source: RuleSource = Field(
        description="Origen principal de la regla: APA7, LOCAL o MIXED.",
    )
    base_standard: str = Field(
        alias="baseStandard",
        description="Nombre del estándar base (normalmente 'APA7').",
    )

    apa_reference: Optional[str] = Field(
        default=None,
        alias="apaReference",
        description="Referencia a la sección/página del manual APA 7.",
    )
    local_reference: Optional[str] = Field(
        default=None,
        alias="localReference",
        description="Referencia a la guía o manual institucional (ej: CUN).",
    )

    severity: Severity = Field(
        description="Severidad cuando la regla no se cumple.",
    )
    check_type: CheckType = Field(
        alias="checkType",
        description="Tipo de validación que requiere la regla.",
    )

    examples: RuleExamples = Field(
        description="Ejemplos de uso correcto e incorrecto de la norma.",
    )
    detection_hints: RuleDetectionHints = Field(
        alias="detectionHints",
        description="Pistas para que el motor pueda detectar esta regla.",
    )

    auto_fix_hint: Optional[str] = Field(
        default=None,
        alias="autoFixHint",
        description="Sugerencia de corrección en lenguaje natural para el usuario.",
    )
    llm_config: Optional[LLMRuleConfig] = Field(
        default=None,
        alias="llmConfig",
        description="Configuración LLM para reglas con checkType='llm_semantic'."
    )


class RuleFile(BaseModel):
    """
    Archivo completo de reglas para un agente y un perfil.

    Forma esperada en cada *.rules.json:

      {
        "profileId": "apa7_cun",
        "agentId": "REFERENCES",
        "rules": [ { ... Rule ... } ]
      }
    """

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )

    profile_id: str = Field(
        alias="profileId",
        description="Identificador del perfil de reglas (ej: 'apa7_cun').",
    )
    agent_id: str = Field(
        alias="agentId",
        description="Identificador del agente (ej: 'REFERENCES').",
    )
    rules: List[Rule] = Field(
        default_factory=list,
        description="Lista de reglas asociadas a este agente y perfil.",
    )
