# Visión General - Motor de Cumplimiento APA7 con Soporte LLM

## 1. Visión del Proyecto

El **Motor de Cumplimiento APA7** es un backend especializado en validación y conformidad con normas APA7 (American Psychological Association, 7ª edición). 

El rol del LLM es **complementario y de soporte**:
- **LLM proporciona**: análisis heurístico, coaching textual, perfilado de documentos
- **Fuente de verdad**: JSON rules + agentes determinísticos (GeneralStructureAgent, etc.)
- **Garantía de calidad**: Las reglas JSON y agentes son el núcleo de validación; el LLM es una capa opcional de enriquecimiento

El LLM **NO es mandatorio** para el funcionamiento del sistema. El backend opera correctamente sin él; las reglas LLM son complementarias.

## 2. Modos de Coach Disponibles

El endpoint `/coach` soporta los siguientes modos operacionales:

### PLAN_SECTION
- **Propósito**: Guiar al usuario en la estructura y planeamiento de una sección académica
- **Entrada**: Contexto del documento, tipo de sección, instrucciones
- **Salida**: Recomendaciones de estructura, puntos clave a cubrir

### REVIEW_SECTION
- **Propósito**: Revisar una sección existente e identificar mejoras
- **Entrada**: Contenido de la sección, normas APA7 aplicables
- **Salida**: Feedback sobre cumplimiento, sugerencias de edición

### CLARIFY
- **Propósito**: Aclarar conceptos específicos de APA7 para el usuario
- **Entrada**: Pregunta o concepto confuso
- **Salida**: Explicación clara y ejemplos si aplican

### DETECT_PROFILE
- **Propósito**: Analizar un documento para detectar patrones de escritura y necesidades del usuario
- **Entrada**: Documento académico completo o parcial
- **Salida**: Perfil de usuario con áreas de mejora identificadas
- **Referencia**: Implementación en PR #1, sirve como patrón de calidad

## 3. Infraestructura de Reglas LLM

Las reglas LLM permiten que ciertos validadores deleguen su lógica a un modelo de lenguaje.

### Estructura de Archivos

**models/rules/**
- Define las clases `Rule` y `RuleFile`
- `Rule`: objeto individual de validación con metadata y configuración LLM opcional
- `RuleFile`: contenedor de múltiples reglas, gestiona serialización JSON

**Configuración LLM en JSON (llmConfig)**

Cada regla JSON puede incluir un campo `llmConfig`:

```json
{
  "id": "rule_123",
  "name": "Check Citation Format",
  "type": "citation",
  "llmConfig": {
    "enabled": true,
    "provider": "openai",
    "model": "gpt-4",
    "temperature": 0.3,
    "prompt_template": "Validate if this citation follows APA7..."
  }
}
```

Campos clave de `llmConfig`:
- `enabled`: Activa/desactiva evaluación LLM para esta regla
- `provider`: Proveedor de LLM (openai, anthropic, etc.)
- `model`: Modelo específico a usar
- `temperature`: Control de creatividad (0-1)
- `prompt_template`: Template de prompt parametrizado

### Clases Principales

**RuleLibrary**
- Carga y gestiona todas las reglas disponibles
- Proporciona acceso por ID o categoría
- Validación de integridad de reglas

**LLMRuleRunner**
- Ejecuta reglas que tienen `llmConfig` habilitado
- Invoca al proveedor LLM configurado
- Cachea resultados si aplica
- Maneja timeouts y errores de red

### Integración con Agentes

**GeneralStructureAgent** e otros agentes cargan reglas JSON mediante RuleLibrary:

```python
rule_library = RuleLibrary()
rule = rule_library.get_rule("rule_123")

if rule.has_llm_config():
    runner = LLMRuleRunner(rule)
    result = runner.execute(document_content)
else:
    result = rule.validate(document_content)  # Validación determinística
```

## 4. Flujo de Ejecución Típico

### Arquitectura General

```
Usuario → /lint (HTTP POST)
         ↓
    LintOrchestrator
         ↓
    Agents (GeneralStructureAgent, etc.)
         ↓
    RuleLibrary.load_rules() [JSON]
         ↓
    Para cada regla con llmConfig:
      - LLMRuleRunner invoca provider
      - Respuesta se integra en resultado
    ↓
    Respuesta de validación → Usuario
```

### Paso a Paso

1. **Request**: Usuario envía documento a `/lint`
2. **Orquestación**: `LintOrchestrator` identifica qué agentes ejecutar
3. **Carga de Reglas**: Agentes cargan `RuleLibrary` desde JSON
4. **Evaluación Determinística**: Reglas sin `llmConfig` se ejecutan directamente
5. **Evaluación LLM**: Reglas con `llmConfig` invocan `LLMRuleRunner`
   - Se prepara el prompt con el template
   - Se invoca al proveedor configurado
   - Se obtiene y procesa la respuesta
6. **Agregación**: Todos los resultados se combinan
7. **Response**: Usuario recibe report de validación con todos los hallazgos

### Punto Clave

**El backend funciona completamente sin LLM**: Si todas las reglas tienen `llmConfig.enabled = false` o no existe `llmConfig`, el sistema usa solo validación determinística JSON + agentes. Las reglas LLM son **aditivas y opcionales**.

## 5. Garantías de Contrato

- ✅ `/lint` endpoint mantiene contrato actual: acepta documento, retorna validaciones
- ✅ `/coach` endpoint mantiene contrato actual: acepta modo + contexto, retorna coaching
- ✅ Nuevas reglas LLM se añaden sin modificar lógica existente
- ✅ Fallback a validación determinística si LLM no está disponible
