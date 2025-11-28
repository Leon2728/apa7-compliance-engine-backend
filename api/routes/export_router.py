"""Router para endpoints de exportación de documentos."""

from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse

from api.models.export_models import ExportDocxRequest
from api.services.export_service import ExportService

# Crear router para exportación
export_router = APIRouter(prefix="/export", tags=["export"])


@export_router.post(
    "/docx",
    status_code=status.HTTP_200_OK,
    summary="Exportar documento a DOCX",
    description="Exporta un documento en formato nativo DOCX (Microsoft Word) con formateo básico APA7.",
    responses={
        200: {"description": "Documento DOCX generado exitosamente"},
        400: {"description": "Solicitud inválida"},
        500: {"description": "Error interno del servidor"},
    },
)
async def export_to_docx(
    request: ExportDocxRequest,
) -> StreamingResponse:
    """Genera un archivo DOCX a partir del texto del documento.
    
    Esta función toma el texto plano del documento y lo convierte en
    un archivo Word (.docx) con formateo básico según los estándares APA7:
    - Márgenes: 1 pulgada en todos los lados
    - Fuente: Times New Roman, 12pt
    - Espaciado: Doble espaciado
    - Sangría: 0.5 pulgadas en la primera línea de cada párrafo
    
    Args:
        request: Objeto ExportDocxRequest con el texto del documento y contexto opcional.
        
    Returns:
        StreamingResponse: Archivo DOCX como descarga de archivo.
    """
    # Llamar al servicio de exportación
    docx_stream = ExportService.export_to_docx(request)
    
    # Devolver como respuesta de streaming con headers de descarga
    return StreamingResponse(
        iter([docx_stream.getvalue()]),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": "attachment; filename=documento_exportado.docx",
            "Content-Type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        },
    )
