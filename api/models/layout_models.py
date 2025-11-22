from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class TableBorders(BaseModel):
    """
    Resumen de bordes de una tabla.

    No es pixel-perfect, pero suficiente para validar:
      - si hay líneas verticales
      - si hay demasiadas líneas horizontales internas
      - si sigue el estilo APA: 3 líneas horizontales, sin verticales.
    """

    model_config = ConfigDict(extra="ignore")

    has_top_border: bool = False
    has_header_bottom_border: bool = False
    has_bottom_border: bool = False

    has_vertical_inner_borders: bool = False
    has_vertical_outer_borders: bool = False
    horizontal_internal_lines_count: int = 0


class TableLayout(BaseModel):
    """Resumen de una tabla detectada en el documento."""

    model_config = ConfigDict(extra="ignore")

    index: int = Field(description="Índice de tabla en el documento (0-based).")
    label: Optional[str] = Field(
        default=None,
        description="Texto tipo 'Tabla 1', si está disponible.",
    )
    title: Optional[str] = None

    borders: TableBorders


class ImageLayout(BaseModel):
    """Resumen de una imagen/figura."""

    model_config = ConfigDict(extra="ignore")

    index: int = Field(description="Índice de imagen en el documento (0-based).")
    label: Optional[str] = Field(
        default=None,
        description="Texto tipo 'Figura 1', si está disponible.",
    )
    caption: Optional[str] = None

    width_cm: float = Field(
        description="Ancho aproximado de la imagen en centímetros.",
    )
    height_cm: float = Field(
        description="Alto aproximado de la imagen en centímetros.",
    )


class DocumentLayout(BaseModel):
    """
    Layout estructural básico del documento:
      - tablas + bordes
      - imágenes + tamaños
    """

    model_config = ConfigDict(extra="ignore")

    tables: List[TableLayout] = Field(default_factory=list)
    images: List[ImageLayout] = Field(default_factory=list)
