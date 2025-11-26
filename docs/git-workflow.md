# Flujo de Trabajo Git y Gobernanza de Cambios

## 1. Convenciones de Ramas

Este repositorio sigue convenciones estrictas para nomenclatura de ramas:

### Tipos de Ramas Permitidas

**feature/...** - Nuevas características
- Ejemplo: `feature/llm-rules-integration`, `feature/new-coach-mode`
- Uso: Implementación de nuevas funcionalidades
- Base: `main`
- Expectativa: PR con descripción clara, tests, documentación

**fix/...** - Correcciones de bugs
- Ejemplo: `fix/coach-timeout-handling`, `fix/citation-validation`
- Uso: Parches de bugs en producción
- Base: `main` (o rama de hotfix si aplica)
- Expectativa: PR con descripción del bug, reproducción, solución

**chore/...** - Cambios de mantenimiento
- Ejemplo: `chore/update-dependencies`, `chore/refactor-logging`
- Uso: Tareas de mantenimiento, actualizaciones, refactor sin cambios funcionales
- Base: `main`
- Expectativa: PR con justificación del cambio

### Ramas Prohibidas

⚠️ **NO trabajar directamente en `main`**
- Todos los cambios DEBEN ir a través de PR
- Branch protection lo impide: se requiere PR + 1 aprobación + CI passing

## 2. Pull Requests - Requerimientos

### Cuándo se Requiere PR

Todos los cambios en los siguientes directorios REQUIEREN PR:

- **api/agents/** - Lógica de agentes de validación
- **api/orchestrator/** - Orquestación de validaciones
- **api/rules/** - Gestión y carga de reglas
- **api/services/coach_service.py** - Servicio de coaching
- **api/models/*** - Modelos de datos
- **docs/** - Documentación del proyecto
- **tests/** - Suite de tests
- **.github/workflows/** - Workflows de CI/CD

### Estructura de PR Recomendada

Cada PR debe incluir:

#### Descripción Breve
Ejemplo:
```
feat: integrar verificación de referencias mediante LLM
```

#### Propósito (Purpose)
Ejemplo:
```
Agrega soporte para validación de referencias bibliográficas 
usando LLMRuleRunner
```

#### Cambios (Changes)
Lista de cambios principales:
```
- Añadido modelos Rule y RuleFile para reglas LLM
- Implementado LLMRuleRunner con soporte para OpenAI
- Integrado con GeneralStructureAgent para validación de referencias
- Añadidos tests unitarios para RuleLibrary
```

#### Detalles de Contrato (Si aplica)
Si el PR modifica endpoints públicos:
```
## Contrato

- GET /coach - SIN cambios
- POST /lint - SIN cambios
- Nuevas reglas JSON se cargan dinámicamente
- Fallback a validación determinística si LLM no disponible
```

#### Checklist
```
- [x] pytest --cov=api tests/ - PASSING
- [x] Documentación actualizada (si cambios públicos)
- [x] NO breaking changes a /lint o /coach
- [x] Commits siguen convención: feat:, fix:, test:, docs:, chore:
- [x] Código revisado para logs y manejo de errores
```

## 3. Protección de Rama Principal (main)

### Reglas Activas en `main`

- **Require pull request reviews before merging**: Sí (1+ approval requerida)
- **Require a pull request before merging**: Sí (todos los cambios DEBEN ser por PR)
- **Add status checks**: Sí (CI workflow `.github/workflows/ci.yml` DEBE pasar)
- **Require branches to be up to date before merging**: Sí
- **Require code owners review**: Futuro (puede añadirse CODEOWNERS)
- **Dismiss stale pull request approvals**: Sí (new commits borran approvals)
- **Require signed commits**: No (opcional, puede habilitarse)
- **Restrict who can push to matching branches**: No (pero es lo ideal)
- **Allow force pushes**: NO (está prohibido)
- **Allow deletions**: NO (está prohibido)

### Flujo de Merge

1. Crear rama feature desde `main`
2. Hacer commits con convención: `feat:`, `fix:`, `test:`, etc.
3. Abrir PR con descripción clara
4. CI automatizado ejecuta tests
5. Al menos 1 revisor aprueba
6. Merge a `main` mediante GitHub UI (squash o merge commit permitido)
7. Rama feature puede ser eliminada después del merge

## 4. Ejemplos de PRs de Calidad

### Referencia 1: PR #1 (DETECT_PROFILE)
**Por qué es bueno:**
- Título descriptivo en español con prefijo convencional
- Descripción clara del objetivo
- Explica patrones de diseño (service encapsulation, thin routers)
- Incluye tests y documentación
- Mantiene coherencia con existente

### Referencia 2: PR #3 (LLM Integration)
**Por qué es bueno:**
- Define claramente qué archivos cambian y por qué
- Explica la infraestructura de reglas LLM
- Especifica que NO hay breaking changes
- 6 commits bien organizados
- 271 adiciones bien estructuradas

## 5. Convenciones de Commits

Utilizar `conventional commits` para mensajes:

### Formatos Válidos

**feat:** Nueva funcionalidad
```
feat: add LLM rule runner for citation validation
```

**fix:** Corrección de bug
```
fix: handle timeout in LLM provider calls
```

**test:** Añadir o modificar tests
```
test: add unit tests for RuleLibrary
```

**docs:** Cambios en documentación
```
docs: add git workflow guide
```

**chore:** Cambios de mantenimiento
```
chore: update pytest dependencies
```

**refactor:** Cambio de código sin alterar funcionalidad
```
refactor: simplify LLMRuleRunner error handling
```

### Formato Extendido (si necesita más contexto)

```
feat: add LLM rule runner

Implement LLMRuleRunner class to execute rules with LLM providers.
Supports OpenAI and Anthropic with configurable temperature and prompts.

Breaking changes: none
Closes: #123
```

## 6. Flujo de Revisión de Código

### Para Autores de PR

1. Antes de abrir PR:
   - Ejecutar `pytest --cov=api tests/` localmente
   - Verificar que todos los tests pasen
   - Revisar el propio código

2. Al abrir PR:
   - Escribir descripción clara y completa
   - Incluir checklist de verificación
   - Especificar si hay breaking changes

3. Durante revisión:
   - Responder todos los comentarios
   - Hacer ajustes solicitados
   - Re-solicitar review después de cambios

### Para Revisores

Al revisar, verificar:
- Tests están presentes y pasan
- Documentación está actualizada
- No hay breaking changes (o están explicitamente documentados)
- Código sigue patrones existentes
- Manejo de errores es adecuado
- Logs son informativos pero no excesivos

## 7. Gestión de Dependencias

Todos los cambios de dependencias REQUIEREN:
- PR separada o incluida con cambios funcionales
- Explicación del motivo de la actualización
- Verificación de compatibilidad
- Tests ejecutándose correctamente

## 8. Versioning

Este proyecto usa semantic versioning (futuro):
- Cambios de API incompatibles: major
- Nuevas funcionalidades compatible: minor
- Fixes y cambios internos: patch

## 9. Preguntas Frecuentes

**P: ¿Puedo hacer force push a main?**
R: NO. Branch protection lo impide. Si necesitas revertir, usa revert.

**P: ¿Puedo mergear sin CI pasando?**
R: NO. CI es requerido y debe pasar.

**P: ¿Cuántas aprobaciones necesito?**
R: Al menos 1. Se recomienda 2 para cambios críticos.

**P: ¿Puedo trabajar en multiple ramas a la vez?**
R: Sí, pero cada rama debe tener su propio PR.
