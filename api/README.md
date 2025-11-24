# Módulo API

## Descripción

Este módulo contiene la capa FastAPI que expone los endpoints HTTP del motor de cumplimiento APA7. Orquesta la ejecución del motor de reglas, agentes especializados, y opcionalmente integra capacidades LLM para enriquecimiento de documentos.

Cuando `LLM_ENABLED=true`, la API carga automáticamente el cliente LLM configurado, permitiendo que los servicios de negocio accedan a capacidades de IA de forma transparente. Cuando `LLM_ENABLED=false`, todos los servicios funcionan sin cambios usando lógica determinista exclusivamente.

## Carpetas principales

- **main.py**: Punto de entrada FastAPI, inicialización de la aplicación y carga de dependencias
- **config.py**: Configuración centralizada incluyendo validación de BaseSettings, variables de entorno y configuración LLM
- **llm/**: Infraestructura LLM (cliente base, proveedores, prompts)
- **services/**: Capa de lógica de negocio que orquesta la validación y opcionalmente utiliza LLM
- **routes/**: Definición de endpoints HTTP (ej: /coach para asistente de coaching)
- **orchestrator/**: Coordinación de múltiples agentes y ejecución de reglas
- **models/**: Esquemas Pydantic para validación de requests/responses
- **agents/**: Agentes especializados para diferentes tipos de validación
- **rules/**: Motor de reglas configurables y evaluación de criterios

## Archivos raíz importantes

- **main.py**: Carga la aplicación FastAPI, rutas, y configuración LLM
- **config.py**: Settings de Pydantic v2 con BaseSettings, variables de entorno

## Integración LLM

La integración LLM es totalmente opcional y controlable mediante:

1. Variable `LLM_ENABLED` en `.env`
2. Configuración de proveedor: `LLM_PROVIDER` (ej: "openai")
3. Credenciales: `LLM_API_KEY`

Los servicios inyectan el cliente LLM solo si está habilitado, manteniendo la compatibilidad hacia atrás completa.
