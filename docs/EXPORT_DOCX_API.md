# Documentación: Endpoint POST /export/docx

## BLOQUE 3 - Exportación de Documentos a DOCX

### Descripción General

El endpoint `POST /export/docx` permite exportar documentos de texto plano a archivos Word (.docx) nativos con formateo básico según los estándares APA7 (American Psychological Association, 7ª edición).

Esta funcionalidad forma parte del motor de cumplimiento APA7 y proporciona a los usuarios la capacidad de descargar sus documentos en un formato ampliamente compatible (Microsoft Word).

### Características Implementadas

1. **Formateo APA7 Básico**
   - Márgenes: 1 pulgada en todos los lados
   - Fuente: Times New Roman, 12pt
   - Espaciado de líneas: Doble espaciado (2.0)
   - Sangría de primera línea: 0.5 pulgadas

2. **Generación en Memoria**
   - El documento se genera completamente en memoria
   - No se crean archivos temporales en el servidor
   - Máximo rendimiento y seguridad

3. **Contexto Flexible**
   - Soporte para metadatos opcionales
   - Posible integración con perfiles APA7
   - Extensible para futuras variantes

### Endpoint

```
POST /export/docx
```

### Modelo de Request

```json
{
  "document_text": "Contenido del documento a exportar...",
  "context": {
    "profile_variant": "apa7_global",
    "metadata": {
      "nivel": "pregrado",
      "tipo_documento": "ensayo"
    }
  }
}
```

#### Parámetros:

- **document_text** (string, requerido): Texto plano completo del documento
- **context** (object, opcional): Contexto para personalizar la exportación
  - **profile_variant** (string, opcional): Variante de perfil APA7
  - **metadata** (object, opcional): Metadatos arbitrarios

### Response

**Status Code: 200 OK**

El servidor retorna:
- **Content-Type**: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- **Content-Disposition**: `attachment; filename=documento_exportado.docx`
- **Body**: Archivo DOCX binario

### Codigos de Error

| Código | Descripción |
|--------|---------------|
| 200 | Documento generado exitosamente |
| 400 | Solicitud inválida (JSON malformado) |
| 422 | Validación de datos fallida |
| 500 | Error interno del servidor |

### Ejemplo de Uso

#### cURL

```bash
curl -X POST http://localhost:8000/export/docx \
  -H "Content-Type: application/json" \
  -d '{
    "document_text": "Esto es un documento de prueba para APA7.",
    "context": {
      "profile_variant": "apa7_global"
    }
  }' \
  --output documento.docx
```

#### Python (requests)

```python
import requests

url = "http://localhost:8000/export/docx"

payload = {
    "document_text": "Contenido del documento...",
    "context": {
        "profile_variant": "apa7_global",
        "metadata": {"nivel": "postgrado"}
    }
}

response = requests.post(url, json=payload)

if response.status_code == 200:
    with open("documento.docx", "wb") as f:
        f.write(response.content)
    print("Documento descargado exitosamente")
else:
    print(f"Error: {response.status_code}")
```

#### JavaScript (fetch)

```javascript
const exportToDocx = async (documentText, context = null) => {
    const payload = {
        document_text: documentText,
        context: context
    };

    try {
        const response = await fetch('/export/docx', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'documento_exportado.docx';
            a.click();
        } else {
            console.error('Error exportando documento');
        }
    } catch (error) {
        console.error('Error:', error);
    }
};
```

### Archivos Implementados

#### 1. **api/models/export_models.py**
Define los modelos Pydantic para validación de datos:
- `ExportDocxContext`: Contexto opcional con metadatos
- `ExportDocxRequest`: Request completo con texto y contexto

#### 2. **api/services/export_service.py**
Implementa la lógica de negocio:
- Clase `ExportService` con método estático `export_to_docx()`
- Generación del documento en memoria
- Formateo APA7 básico

#### 3. **api/routes/export_router.py**
Define el endpoint FastAPI:
- Router con prefijo `/export`
- Endpoint `POST /export/docx`
- Respuesta como `StreamingResponse`

#### 4. **api/main.py** (Modificado)
Registra el router en la aplicación FastAPI

#### 5. **requirements.txt** (Actualizado)
Añadida dependencia: `python-docx>=1.0.0`

### Flujo de Ejecución

```
Request JSON
    |
    v
Validación con Pydantic (ExportDocxRequest)
    |
    v
Llamada a ExportService.export_to_docx()
    |
    v
Creación documento Word en memoria
    |
    v
Aplicación de estilos APA7
    |
    v
Guardado en BytesIO
    |
    v
Retorno como StreamingResponse
    |
    v
Descarga de archivo DOCX
```

### Consideraciones Futuras

1. **Formateo Avanzado**
   - Numeración de páginas
   - Encabezados y pies de página
   - Índices automáticos

2. **Validación de Contenido**
   - Validación de estructura APA7
   - Detección de errores de formato
   - Sugerencias de corrección

3. **Soporte Adicional**
   - Exportación a PDF
   - Exportación a ODT (OpenDocument)
   - Bátch de múltiples documentos

4. **Optimización**
   - Caché de documentos generados
   - Comprimisión de archivos grandes
   - Limite de tamaño máximo

### Testing

La funcionalidad se puede probar mediante:

1. **Swagger UI**: `http://localhost:8000/docs`
2. **ReDoc**: `http://localhost:8000/redoc`
3. **Herramientas de línea de comandos**: cURL, httpie
4. **Clientes HTTP**: Postman, Insomnia

### Dependencias

- **FastAPI** (>=0.104.0): Framework web
- **Pydantic** (>=2.0): Validación de datos
- **python-docx** (>=1.0.0): Generación de documentos Word

### Notas Importantes

1. El documento se genera íntegramente en memoria, sin crear archivos temporales
2. El formateo es básico; no incluye tídlos, referencias ni citas automáticas
3. El contexto es flexible y extensible para futuros requerimientos
4. Los metadatos en el contexto se pueden usar para filtrar o personalizar el formato

### Contacto y Soporte

Para preguntas o sugerencias sobre este endpoint, por favor abre un issue en el repositorio.
