# Changelog

All notable changes to this project will be documented in this file.

## [0.3.0-alpha] - 2025-11-25

### Nueva Funcionalidad
- **Integración de Reglas LLM** (PR #3): Sistema de reglas semánticas con soporte para Language Models
  - LLMRuleRunner para ejecución de reglas basadas en LLM
  - Configuración llmConfig para reglas LLM
  - Integración con GeneralStructureAgent
  - Demo rule: CUM-GS-LLM-001

- **Pruebas de Infraestructura LLM** (PR #7): Cobertura QA completa
  - 13 métodos de test para infraestructura LLM
  - TestRuleFileHandling, TestRuleLibrary, TestLLMRuleRunner
  - Validación de contratos /lint y /coach
  - Todas las pruebas con mocks (sin dependencias LLM reales)

### Infraestructura
- **CI/CD Workflow** (PR #2): Automatización pytest
  - Python 3.9, 3.10, 3.11
  - Estado requerido para merge en main
  - Branch protection activada

### Documentación
- **LLM Overview** (PR #5): Arquitectura de integración LLM
  - Componentes LLM (runners, agentes, configuración)
  - Modelo de reglas con soporte semántico
  - Ejemplos de uso

- **Git Workflow Governance** (PR #6): Guía de branching y protección
  - Protección de rama main
  - Estándares de commit convencional
  - Proceso de PR y revisión
  - Historial de ramas legacy

### Gobernanza
- **Protección de Rama Main**:
  - PR requerido (mínimo 1 approval)
  - CI checks obligatorios
  - Block force push & branch deletions

- **Limpieza de Ramas**: Decisiones sobre ramas LLM legacy
  - feature/llm-rules-tests: Obsoleta, sustituida por PR #7
  - feature/llm-backend-integration: Parcialmente útil, documentada

### Limitaciones Conocidas
- API sujeta a cambios menores en futuras versiones
- No optimizado para alta carga (v1.0 será versión de producción)
- Algunas validaciones LLM dependen de configuración externa
- Timeouts de LLM no están finamente tuneados

### Criterios de Estabilidad
- ✅ CI verde en Python 3.9/3.10/3.11
- ✅ Todos los 5 PRs mergeados
- ✅ NO breaking changes en /lint y /coach
- ✅ Documentación sincronizada con código
- ✅ Cobertura de tests para infraestructura LLM

## [0.2.0] - Anteriormente
- Infraestructura básica
- Modelos de datos
- Agentes de validación
