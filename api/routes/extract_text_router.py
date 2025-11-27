"""Router para el endpoint /extract-text.

Permite subir documentos (.txt, .docx, .pdf, .odt) y extraer su texto.
"""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from api.models.extract_text_models import ExtractTextResponse
from api.services.text_extraction_service import extract_text_from_bytes

router = APIRouter(prefix="/extract-text", tags=["extract-text"])


@router.post("", response_model=ExtractTextResponse)
async def extract_text_endpoint(file: UploadFile = File(...)) -> ExtractTextResponse:
    """
    Extrae el texto de un documento subido.

    Soporta formatos: .txt, .docx, .pdf (parcialmente .odt).

    Args:
        file: Archivo subido (multipart/form-data).

    Returns:
        ExtractTextResponse con el texto extraído y metadata.

    Raises:
        HTTPException(400): Si no se puede leer el archivo.
    """
    try:
        content = await file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail="No se pudo leer el archivo subido"
        ) from exc

    text, warnings = extract_text_from_bytes(
        content=content,
        filename=file.filename,
        content_type=file.content_type,
    )

    return ExtractTextResponse(
        text=text,
        file_name=file.filename,
        file_type=file.content_type,
        warnings=warnings,
    )
