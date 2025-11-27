from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ExtractTextResponse(BaseModel):
    """
    Respuesta del endpoint /extract-text.
    Contiene el texto extraído del documento y metadata básica.
    """

    model_config = ConfigDict(extra="ignore")

    text: str = Field(..., description="Texto extraído del documento")
    file_name: str | None = Field(None, description="Nombre del archivo subido")
    file_type: str | None = Field(
        None, description="Content-Type del archivo (MIME type)"
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Lista de advertencias durante la extracción (ej. PDF sin texto)",
    )
