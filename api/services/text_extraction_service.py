"""Servicio de extracción de texto de documentos.

Soporta múltiples formatos: .txt, .docx, .pdf, .odt.
"""

from __future__ import annotations

import io
from pathlib import Path


def extract_text_from_bytes(
    content: bytes,
    filename: str | None = None,
    content_type: str | None = None,
) -> tuple[str, list[str]]:
    """
    Extrae texto de un archivo binario.

    Args:
        content: Contenido binario del archivo.
        filename: Nombre del archivo (para inferir tipo por extensión).
        content_type: MIME type (ej. 'application/pdf').

    Returns:
        Tupla (texto_extraído, lista_de_warnings).

    Soporta:
        - .txt: decodificación UTF-8 con fallback a latin-1.
        - .docx: usando python-docx.
        - .pdf: usando PyPDF2 (advertencia si no hay texto).
        - .odt: advertencia (no completamente soportado aún).
    """
    warnings: list[str] = []

    # Determinar extensión del archivo
    extension = _infer_extension(filename, content_type)

    # Despachar según tipo
    if extension == ".txt":
        text = _extract_from_txt(content, warnings)
    elif extension == ".docx":
        text = _extract_from_docx(content, warnings)
    elif extension == ".pdf":
        text = _extract_from_pdf(content, warnings)
    elif extension == ".odt":
        text = _extract_from_odt(content, warnings)
    else:
        warnings.append(
            f"Tipo de archivo no soportado: {extension or 'desconocido'}. "
            "Formatos soportados: .txt, .docx, .pdf"
        )
        text = ""

    return text, warnings


def _infer_extension(filename: str | None, content_type: str | None) -> str | None:
    """Infiere la extensión del archivo desde filename o content_type."""
    # Primero intentar desde filename
    if filename:
        ext = Path(filename).suffix.lower()
        if ext:
            return ext

    # Fallback a content_type
    if content_type:
        mime_to_ext = {
            "text/plain": ".txt",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
            "application/pdf": ".pdf",
            "application/vnd.oasis.opendocument.text": ".odt",
        }
        return mime_to_ext.get(content_type.lower())

    return None


def _extract_from_txt(content: bytes, warnings: list[str]) -> str:
    """Extrae texto de un archivo .txt plano."""
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return content.decode("latin-1")
        except Exception as exc:
            warnings.append(f"Error al decodificar archivo TXT: {exc}")
            return ""


def _extract_from_docx(content: bytes, warnings: list[str]) -> str:
    """Extrae texto de un archivo .docx usando python-docx."""
    try:
        import docx
    except ImportError:
        warnings.append(
            "Librería 'python-docx' no instalada. No se puede extraer texto de DOCX."
        )
        return ""

    try:
        file_stream = io.BytesIO(content)
        doc = docx.Document(file_stream)
        paragraphs = [para.text for para in doc.paragraphs]
        return "\n".join(paragraphs)
    except Exception as exc:
        warnings.append(f"Error al extraer texto de DOCX: {exc}")
        return ""


def _extract_from_pdf(content: bytes, warnings: list[str]) -> str:
    """Extrae texto de un archivo PDF usando PyPDF2."""
    try:
        import PyPDF2
    except ImportError:
        warnings.append(
            "Librería 'PyPDF2' no instalada. No se puede extraer texto de PDF."
        )
        return ""

    try:
        file_stream = io.BytesIO(content)
        reader = PyPDF2.PdfReader(file_stream)
        text_parts = []

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

        text = "\n".join(text_parts)

        # Advertir si el PDF no contiene texto
        if not text.strip():
            warnings.append(
                "El PDF no contiene texto extraíble (puede ser solo imágenes)."
            )

        return text
    except Exception as exc:
        warnings.append(f"Error al extraer texto de PDF: {exc}")
        return ""


def _extract_from_odt(content: bytes, warnings: list[str]) -> str:
    """Extrae texto de un archivo .odt (placeholder para futuro soporte)."""
    # Soporte completo de ODT requiere librerías adicionales (odfpy, etc.)
    # Por ahora, devolver warning y texto vacío
    warnings.append(
        "Formato ODT aún no está completamente soportado. "
        "Considere convertir el archivo a DOCX o PDF."
    )
    return ""
