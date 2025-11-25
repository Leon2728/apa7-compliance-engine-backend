# api/models/profile_models.py

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class ApaKind(str, Enum):
    student = "student"
    professional = "professional"
    unknown = "unknown"


class DocumentType(str, Enum):
    tesis = "tesis"
    informe = "informe"
    ensayo = "ensayo"
    articulo = "articulo"
    reporte_investigacion = "reporte_investigacion"
    otro = "otro"


class DocumentLevel(str, Enum):
    pregrado = "pregrado"
    posgrado = "posgrado"
    profesional = "profesional"
    escolar = "escolar"
    otro = "otro"


class DocumentMode(str, Enum):
    individual = "individual"
    grupal = "grupal"
    desconocido = "desconocido"


class DocumentProfileAnalysis(BaseModel):
    """
    Resultado estructurado del clasificador/detector de perfil de documento.

    Este modelo está pensado para mapear 1:1 con el JSON que devuelve el LLM
    y que el frontend pueda consumir fácilmente.
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    is_academic: bool = Field(..., alias="isAcademic")

    apa_kind: ApaKind = Field(..., alias="apaKind")

    # Tipo de documento: tesis, informe, ensayo, etc. Puede ser None si no está claro.
    document_type: Optional[DocumentType] = Field(
        default=None,
        alias="documentType",
    )

    # Nivel educativo: pregrado, posgrado, etc.
    level: Optional[DocumentLevel] = Field(
        default=None,
        alias="level",
    )

    # Modalidad: individual / grupal / desconocido
    mode: Optional[DocumentMode] = Field(
        default=None,
        alias="mode",
    )

    # Confianza del clasificador: 0.0 – 1.0
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        alias="confidence",
    )

    # ID de perfil sugerido, por ejemplo: "apa7_cun_informe_pregrado_grupal"
    suggested_profile_id: Optional[str] = Field(
        default=None,
        alias="suggestedProfileId",
    )

    # Razones textuales que explican la clasificación
    reasons: List[str] = Field(
        default_factory=list,
        alias="reasons",
    )
