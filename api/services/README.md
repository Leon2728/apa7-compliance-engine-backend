# Módulo Services

## Descripción

Este módulo contiene la capa de lógica de negocio que orquesta la validación de documentos y opcionalmente integra capacidades LLM. Los servicios implementan la lógica de decisión sobre cómo y cuándo utilizar LLM.

Cada servicio recibe el cliente LLM inyectado (o `None` si está deshabilitado) y decide automáticamente si usarlo según la lógica de negocio. Esta separación garantiza que:

1. La lógica de negocio es independiente de si LLM está disponible
2. Siempre existe un path determinista (fallback)
3. Los endpoints nunca conocen sobre LLM; todo es transparente

## CoachService

### Rol
Implenta la lógica del asistente de coaching para ayudar a usuarios a mejorar documentos académicos en formato APA7.

### Inyección de dependencias
```python
def __init__(self, llm_client: Optional[BaseLLMClient] = None):
    self.llm_client = llm_client  # Puede ser None si LLM_ENABLED=false
```

### Lógica de decisión
Para cada solicitud de coaching:
1. Evalúa si LLM está disponible: `if self.llm_client is not None`
2. Si está disponible: utiliza LLM para generar sugerencias contextual
3. Si NO está disponible: aplica lógica determinista de reglas de coaching

### Ejemplo de uso desde router
```python
coach_service = CoachService(llm_client=get_llm_client())
response = await coach_service.generate_coaching(request)
# El servicio maneja automáticamente si usar o no LLM
```

## Patrón general para servicios

Cada servicio debe seguir este patrón:

1. **Inyección**: Recibir `Optional[BaseLLMClient]` en `__init__`
2. **Lógica**: Chequear `if self.llm_client is not None` antes de usarlo
3. **Fallback**: Siempre tener una implementación determinista alternativa
4. **Transparencia**: Nunca exponer la decisión LLM vs determinista en la API

## Relación con otros módulos

- **api.config**: Lee `LLM_ENABLED` para decidir si crear la instancia LLMClient
- **api.llm**: Utiliza el cliente LLM inyectado
- **api.routes**: Envía requests a servicios, que manejan LLM internamente
- **api.rules**: Capa determinista que los servicios pueden usar como fallback
- **api.orchestrator**: Coordina múltiples agentes; utiliza servicios para lógica específica
