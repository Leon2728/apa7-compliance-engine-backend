# Módulo LLM

## Descripción

Este módulo contiene la infraestructura para integración con proveedores de Modelos de Lenguaje (LLM). Proporciona abstracciones genéricas y adaptadores concretos para diferentes proveedores (OpenAI, etc.).

La integración es completamente opcional. Cuando `LLM_ENABLED=false`, este módulo no se inicializa y los servicios operan con lógica determinista exclusivamente.

## Componentes principales

### __init__.py
Exporta la interfaz pública del módulo LLM.

### client.py
Define la infraestructura base:
- **BaseLLMClient**: Clase abstracta que define la interfaz de cliente LLM
- **ChatMessage**: Estructura para representar mensajes en conversación
- **LLMResponse**: Estructura para respuestas del LLM (contenido, metadata, etc.)
- **LLMClientError**: Excepciones específicas de errores LLM

Todos los clientes de LLM deben heredar de `BaseLLMClient` e implementar los métodos abstractos.

### providers.py
Implementaciones concretas de clientes LLM:
- **OpenAILLMClient**: Cliente para OpenAI, maneja autenticación, request/response, manejo de errores
- Cada proveedor implementa: `async_chat()`, `validate_config()`, manejo de retries

### prompts/
Contiene plantillas de prompts organizadas por caso de uso:
- **coach/plan_section_es.md**: Prompt para generación de secciones de plan de coaching en español
- Los prompts son estáticos, cargados en tiempo de inicialización

## Rol en la arquitectura

El módulo LLM es **infraestructura, no lógica de negocio**:
1. Los servicios (ej: CoachService) reciben el cliente LLM inyectado (o None si está deshabilitado)
2. Los servicios decîden si usar LLM basado en lógica de negocio
3. Los endpoints NUNCA llaman LLM directamente; siempre a través de servicios
4. Las reglas de negocio NO dependen de LLM; siempre tienen fallback determinístico

## Configuración

Controla mediante variables de entorno en `config.py`:
- `LLM_ENABLED`: Booleano para habilitar/deshabilitar
- `LLM_PROVIDER`: Nombre del proveedor ("openai")
- `LLM_API_KEY`: Clave API del proveedor
- `LLM_MODEL`: Modelo a usar (ej: "gpt-4")

Cuando `LLM_ENABLED=false`, todas estas variables son ignoradas.
