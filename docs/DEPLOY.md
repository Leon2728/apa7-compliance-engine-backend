# Despliegue del Backend APA7 Compliance Engine

Esta guía explica cómo desplegar el backend de APA7 Compliance Engine en producción usando **Render** y cómo configurar tu frontend (Lovable.ai) para conectarse a él.

## Resumen Rápido

| Componente | Detalles |
|-----------|----------|
| **Backend** | FastAPI en Python |
| **Plataforma recomendada** | Render (gratis con plan free) |
| **Configuración** | render.yaml en la raíz del repo |
| **Endpoint principal** | POST /lint |
| **URL del backend** | https://{service-name}.onrender.com |

---

## Paso 1: Preparación (Debe hacer el administrador del backend)

### Requisitos

- Cuenta en [Render.com](https://render.com)
- Acceso al repositorio de GitHub
- El archivo `render.yaml` ya está incluido en el repo ✅

### Conexión del Repositorio a Render

1. **Inicia sesión en Render.com**
   - Ve a https://render.com
   - Usa tu cuenta de GitHub para iniciar sesión

2. **Crear nuevo servicio web**
   - Haz clic en "New" en la esquina superior derecha
   - Selecciona "Web Service"
   - Conecta tu repositorio de GitHub
   - Selecciona: `Leon2728/apa7-compliance-engine-backend`

3. **Configuración del Servicio**
   - **Name**: `apa7-compliance-engine` (o similar)
   - **Environment**: Python
   - **Build Command**: Render leerá automáticamente desde `render.yaml`
   - **Start Command**: Render leerá automáticamente desde `render.yaml`
   - **Plan**: Free (recomendado para testing/desarrollo)

4. **Deploy**
   - Haz clic en "Create Web Service"
   - Render automáticamente:
     - Instalará dependencias (pip install -r requirements.txt)
     - Iniciará el servidor (uvicorn api.main:app --host 0.0.0.0 --port $PORT)
     - Te asignará una URL pública

---

## Paso 2: Obtener la URL del Backend

### Dónde encontrar tu URL pública

1. En el dashboard de Render, ve a tu servicio `apa7-compliance-engine`
2. En la sección "Logs" o en la parte superior del dashboard, verás una URL como:
   ```
   https://apa7-compliance-engine.onrender.com
   ```
3. Esta URL es tu **URL base del backend**

### Verificar que funciona

Abre en tu navegador:
```
https://{tu-url}.onrender.com/health
```

Deberías ver una respuesta JSON como:
```json
{
  "status": "ok",
  "timestamp": "2025-01-23T14:30:42.123456",
  "rule_agents": ["GENERALSTRUCTURE", "GLOBALFORMAT", ...]
}
```

O prueba con curl:
```bash
curl https://{tu-url}.onrender.com/health
```

---

## Paso 3: Configurar el Frontend (Lovable.ai)

### Configuración de Variables de Entorno

En tu proyecto de Lovable.ai, añade esta variable de entorno en tu archivo `.env` o `.env.local`:

```
VITE_APA7_BACKEND_URL=https://{tu-url}.onrender.com
```

Reemplaza `{tu-url}` con tu URL real del backend.

**Ejemplo:**
```
VITE_APA7_BACKEND_URL=https://apa7-compliance-engine.onrender.com
```

### Código TypeScript para llamar al endpoint

En tu componente React/Lovable, importa y usa la función:

```typescript
import { useLintDocument } from '@/services/lintService';

function DocumentValidator() {
  const { validate, loading, error, response } = useLintDocument();

  const handleValidate = async () => {
    try {
      const result = await validate(
        "Tu texto del documento aquí...",
        {
          document_type: "tesis_trabajo_grado",
          language: "es",
          profile_variant: "cun_official"
        }
      );
      
      console.log("Validación completada:", result);
      console.log("Errores:", result.summary.error_count);
      console.log("Advertencias:", result.summary.warning_count);
    } catch (err) {
      console.error("Error en validación:", err);
    }
  };

  return (
    <div>
      <button onClick={handleValidate} disabled={loading}>
        {loading ? 'Validando...' : 'Validar Documento'}
      </button>
      {error && <p className="error">{error}</p>}
    </div>
  );
}
```

---

## Paso 4: Probar la Integración

### Opción A: Desde Postman o curl

```bash
curl -X POST https://{tu-url}.onrender.com/lint \
  -H "Content-Type: application/json" \
  -d '{
    "document_text": "TÍTULO\n\nRESUMEN\nEste es un documento de prueba.",
    "context": {
      "language": "es",
      "profile_variant": "cun_official"
    }
  }'
```

### Opción B: Desde Lovable.ai

1. Abre tu proyecto en Lovable
2. Asegúrate de que `VITE_APA7_BACKEND_URL` esté configurado
3. Llama a tu función de validación
4. Verifica los logs del navegador (F12) para ver la respuesta

---

## Solución de Problemas

### El backend no responde / Error 503

**Causa**: El servicio en Render podría estar durmiendo (en plan free se duerme después de 15 min de inactividad).

**Solución**: El primer hit tarda ~1 minuto en iniciar. Espera unos segundos y reintentar.

### Error CORS

**Causa**: El frontend no puede llamar al backend por restricciones del navegador.

**Solución**: Este backend NO tiene CORS configurado por defecto. Si necesitas llamar desde otro dominio, contacta al equipo backend para añadir:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-lovable-domain.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Error 404 en /lint

**Causa**: URL incorrecta del backend.

**Solución**: Verifica que `VITE_APA7_BACKEND_URL` sea exacta (sin trailing slash):
```
✅ https://apa7-compliance-engine.onrender.com
❌ https://apa7-compliance-engine.onrender.com/
```

---

## URLs Importantes

| Recurso | URL |
|---------|-----|
| **API Docs (Swagger)** | `https://{tu-url}.onrender.com/docs` |
| **API Docs (ReDoc)** | `https://{tu-url}.onrender.com/redoc` |
| **Health Check** | `https://{tu-url}.onrender.com/health` |
| **Endpoint Principal** | `https://{tu-url}.onrender.com/lint` |
| **Dashboard Render** | https://dashboard.render.com |

---

## RESUMEN FINAL PARA EL FRONTEND

**Después de desplegar en Render:**

1. Copia la URL pública que Render te asigna (ej: `https://apa7-compliance-engine.onrender.com`)
2. En tu `.env` de Lovable, establece:
   ```
   VITE_APA7_BACKEND_URL=https://apa7-compliance-engine.onrender.com
   ```
3. Tu frontend llamará a: `{VITE_APA7_BACKEND_URL}/lint` con POST
4. ¡Listo! Tu frontend está conectado al backend.
