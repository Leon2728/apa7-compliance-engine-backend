"""Servicio de exportación de documentos a formatos nativos (DOCX, PDF, etc.)."""

from io import BytesIO
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from typing import BinaryIO

from api.models.export_models import ExportDocxRequest


class ExportService:
    """Servicio de exportación de documentos."""

    @staticmethod
    def export_to_docx(request: ExportDocxRequest) -> BinaryIO:
        """Exporta un documento de texto plano a formato DOCX nativo APA7.
        
        Args:
            request: Objeto ExportDocxRequest con el texto del documento y contexto.
            
        Returns:
            BytesIO: Archivo DOCX en memoria listo para descargar.
        """
        # Crear un nuevo documento Word
        doc = Document()
        
        # Configurar estilos básicos de APA7
        # 1. Márgenes (1 pulgada en todos los lados)
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)
        
        # 2. Fuente predeterminada: Times New Roman, 12pt
        style = doc.styles['Normal']
        style.font.name = 'Times New Roman'
        style.font.size = Pt(12)
        style.paragraph_format.line_spacing = 2.0  # Doble espaciado
        style.paragraph_format.space_after = Pt(0)  # Sin espacios adicionales entre párrafos
        
        # Procesar el texto del documento
        # Para simplificar, dividimos el texto por párrafos (líneas en blanco)
        paragraphs = request.document_text.split('\n')
        
        for para_text in paragraphs:
            if para_text.strip():  # Solo añadir párrafos no vacíos
                p = doc.add_paragraph(para_text.strip())
                # Aplicar formateo APA7 básico
                for run in p.runs:
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(12)
                # Sangría de primera línea: 0.5 pulgadas
                p.paragraph_format.first_line_indent = Inches(0.5)
                p.paragraph_format.line_spacing = 2.0
        
        # Guardar el documento en memoria
        docx_stream = BytesIO()
        doc.save(docx_stream)
        docx_stream.seek(0)  # Reiniciar el puntero al inicio del archivo
        
        return docx_stream
