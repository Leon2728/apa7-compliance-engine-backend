# APA7 Compliance Engine Backend

Un backend especializado en validación y conformidad con normas APA7 (American Psychological Association, 7ª edición), desarrollado en **FastAPI**.

## 📋 Descripción

Este proyecto implementa un motor de cumplimiento (compliance engine) para verificar documentos, referencias y citas según los estándares APA7. Incluye:

- **Motor de reglas**: Validación flexible basada en reglas configurables
- **Agentes especializados**: Módulos específicos para diferentes tipos de validación
- **Orquestador**: Coordinación de múltiples agentes
- **API REST**: Interfaz HTTP para integración externa

## 🚀 Inicio rápido

### Requisitos previos

- Python 3.9+
- pip o uv (gestor de paquetes)

### Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/tu-usuario/apa7-compliance-engine-backend.git
   cd apa7-compliance-engine-backend
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

   O si usas `pyproject.toml`:
   ```bash
   pip install -e .
   ```

### Ejecutar el servidor

```bash
python -m api.main
```

O directamente:
```bash
uvicorn api.main:app --reload
```

El servidor estará disponible en: **`http://localhost:8000`**

Accede a la documentación interactiva en: **`http://localhost:8000/docs`**

## 🧪 Pruebas

Ejecutar todas las pruebas:
```bash
pytest
```

Con cobertura:
```bash
pytest --cov=api tests/
```

## 📁 Estructura del proyecto

```
api/
├── main.py              # Aplicación FastAPI principal
├── rules_models.py      # Modelos de datos para reglas
├── rules_library.py     # Biblioteca de reglas APA7
├── agents/              # Agentes especializados
├── orchestrator/        # Orquestador de agentes
├── models/              # Modelos adicionales
└── rules/
    └── apa7_cun/        # Reglas específicas APA7
tests/                   # Suite de pruebas
```

## 📚 Documentación

- **API Docs**: `http://localhost:8000/docs` (Swagger)
- **ReDoc**: `http://localhost:8000/redoc`

## 🤖 Configuración del LLM (Opcional)

Esta versión incluye soporte opcional para integración con modelos de lenguaje (LLM) a través de OpenAI. El sistema funciona perfectamente sin LLM habilitado.

### Variables de Entorno

#### LLM_ENABLED
- **Default:** `false`
- **Descripción:** Activa o desactiva la funcionalidad de coaching asistido por IA.
- **Valores:** `true`, `false`, `1`, `0`, `yes`, `no`
- **Comportamiento:**
  - `false` → Motor de reglas standard, /coach retorna respuestas genéricas de fallback
  - `true` → /coach utiliza OpenAI para coaching inteligente (requiere OPENAI_API_KEY)

#### OPENAI_API_KEY
- **Default:** Vacío
- **Descripción:** Tu clave API de OpenAI (obtener en https://platform.openai.com/api-keys)
- **Requerido:** Sólo si `LLM_ENABLED=true`
- **Nota de Seguridad:** Nunca comitees esta clave; usa variables de entorno o secrets en CI/CD

#### OPENAI_MODEL
- **Default:** `gpt-4`
- **Descripción:** Modelo de OpenAI a utilizar
- **Opciones:** `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo`, etc.
- **Requerido:** No (solo cuando LLM_ENABLED=true)

#### OPENAI_TIMEOUT
- **Default:** `30` segundos
- **Descripción:** Tiempo máximo de espera para llamadas a OpenAI API
- **Requerido:** No

### Comportamiento Esperado

#### Escenario 1: LLM Deshabilitado (Default)
```bash
LLM_ENABLED=false
```
**Resultado:**
- ✅ App arranca sin problemas
- ✅ /lint funciona (sin cambios)
- ✅ /health funciona (sin cambios)
- ✅ /coach disponible pero retorna respuestas fallback genéricas
- ✅ Cero dependencias en OpenAI - no requiere OPENAI_API_KEY

#### Escenario 2: LLM Habilitado con Credenciales Válidas
```bash
LLM_ENABLED=true
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
```
**Resultado:**
- ✅ App arranca normalmente
- ✅ /lint funciona (sin cambios)
- ✅ /coach utiliza OpenAI para coaching inteligente
- ✅ Respuestas contextuales y personalizadas por IA

#### Escenario 3: LLM Habilitado pero sin API Key
```bash
LLM_ENABLED=true
OPENAI_API_KEY=  # Vacío
```
**Resultado:**
- ✅ App arranca (degradación elegante)
- ✅ /lint funciona (sin cambios)
- ✅ /coach retorna respuestas fallback (sin errores)
- ✅ Logs indican que LLM no está disponible

### Ejemplo: .env para Desarrollo

```
# Sólo reglas, sin LLM
LLM_ENABLED=false

# O, con LLM en staging/producción (ocultar en .gitignore)
# LLM_ENABLED=true
# OPENAI_API_KEY=sk-tu-clave-aqui
# OPENAI_MODEL=gpt-4
# OPENAI_TIMEOUT=30

DEBUG=false
```

### Recomendaciones de Despliegue

1. **Desarrollo Local:** Mantener `LLM_ENABLED=false` para evitar dependencias externas
2. **Testing:** Probar con `LLM_ENABLED=false` primero, luego con `true` en ambiente de staging
3. **Producción:** 
   - ⚠️ Inicialmente dejar `LLM_ENABLED=false`
   - ✅ Monitorear logs en staging con LLM habilitado
   - ✅ Solo activar en producción después de validación exhaustiva
   - ✅ Usar secrets manager para OPENAI_API_KEY
   - ✅ Tener plan de rollback (cambiar flag a false instantáneamente)

### Endpoints Afectados

- **GET /health** → Sin cambios
- **POST /lint** → Sin cambios (LLM integración futura)
- **POST /coach** → Nuevo; delega a CoachService que usa LLM si está disponible



## 🏗️ Arquitectura del backend

Este backend integra un motor de cumplimiento APA7+CUN con soporte opcional para LLM. La arquitectura sigue principios SOLID con clara separación de responsabilidades:

```text
apa7-compliance-engine-backend/
├── api/
│   ├── main.py                    # Aplicación FastAPI principal
│   ├── config.py                  # Configuración y feature flags (LLM_ENABLED)
│   ├── principal.py               # Punto de entrada de la app
│   ├── llm/
│   │   ├── __init__.py            # Exportaciones del módulo LLM
│   │   ├── client.py              # Interfaz abstracta BaseLLMClient
│   │   ├── providers.py           # Implementación OpenAILLMClient
│   │   └── prompts/
│   │       └── coach/
│   │           └── plan_section_es.md
│   ├── services/
│   │   └── coach_service.py       # Servicio de coaching con LLM
│   ├── routes/
│   │   ├── __init__.py            # Rutas paquete init
│   │   └── coach_router.py        # Router del endpoint /coach
│   ├── orchestrator/
│   │   └── lint_orchestrator.py   # Orquestador de agentes
│   ├── models/
│   │   ├── coach/
│   │   └── lint_models.py         # Modelos Pydantic
│   ├── agents/                    # Agentes de validación
│   ├── rules/                     # Motor de reglas
│   │   └── apa7_cun/              # Reglas APA7+CUN
│   └── normas/                    # Normativas y estándares
├── tests/                          # Suite de pruebas
├── docs/                           # Documentación
├── .env.example                    # Variables de entorno
├── pyproject.toml                  # Configuración
├── requirements.txt                # Dependencias
└── README.md                       # Este archivo
```

### Componentes Clave

- **Motor de Reglas**: Validación flexible basada en reglas configurables (APA7+CUN)
- **Agentes**: Módulos independientes para diferentes tipos de validación
- **Orquestador**: Coordina múltiples agentes y ejecuta la lógica del compliance engine
- **API REST**: Endpoints FastAPI (/lint, /coach, /health)
- **LLM Opcional**: Infraestructura LLM activada con `LLM_ENABLED=true`



## 🤝 Contribuciones

Por favor, lee [CONTRIBUTING.md](./CONTRIBUTING.md) para conocer nuestras directrices.

## 📄 Licencia

Este proyecto está bajo la licencia [MIT](./LICENSE).

## 📧 Contacto

Para preguntas o sugerencias, abre un issue en el repositorio.

---

**Estado**: En desarrollo 🚧
