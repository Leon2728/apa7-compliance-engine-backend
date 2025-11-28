"""Modelos Pydantic para exportación de documentos a formatos nativos."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict, Optional


class ExportDocxContext(BaseModel):
    """Contexto opcional para enriquecer la exportación a DOCX.

    Por ahora lo usaremos de forma mínima, pero a futuro puede incluir:
    - profile_variant (apa7_global / apa7_institutional / apa7_both)
    - metadatos académicos
    - información de curso / institución
    """

    model_config = ConfigDict(extra="allow")

    profile_variant: Optional[str] = Field(
        default=None,
        description="Variante de perfil usada para formateo APA (ej. apa7_global, apa7_institutional).",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadatos arbitrarios que el frontend quiera enviar (nivel, tipo de documento, etc.).",
    )


class ExportDocxRequest(BaseModel):
    """Request para exportar un documento en formato DOCX nativo."""

    model_config = ConfigDict(extra="ignore")

    document_text: str = Field(
        ...,
        description="Texto plano completo del documento a exportar.",
    )
    context: Optional[ExportDocxContext] = Field(
        default=None,
        description="Contexto opcional para personalizar el formato APA.",
    )
