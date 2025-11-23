# APA7-CUN Rules Registry

## Perfiles y variantes

- **profileId**: `"apa7_cun"` es el perfil base para toda la arquitectura de linting.
- **profile_variant**: Define cómo se aplican las reglas según el contexto académico:
  - `"cun_official"` → Aplica todas las reglas, incluyendo las locales (source=`"LOCAL"`). Para documentos CUN oficial.
  - `"apa7_international"` → Los agentes basados en reglas saltan automáticamente las reglas con source=`"LOCAL"`, aplicando solo reglas estándar APA7.

### Implementación técnica

Esta lógica se implementa mediante:
- Uso de `RuleSource.LOCAL` en los modelos de reglas.
- Chequeo en cada agente: `if is_international and rule.source == RuleSource.LOCAL: continue`
- `context.profile_variant` es propagado desde el `LintRequest` → `LintContext` en el endpoint `/lint`.

---

## Agentes y archivos de reglas

| Agent ID | Clase Python | Archivo JSON | Rango de reglas | Tipo de documento | Qué valida |
|----------|-------------|--------------|------------------|----|--------|
| GENERALSTRUCTURE | GeneralStructureAgent | general-structure.rules.json | CUN-GS-001–CUN-GS-006 | todos | Estructura general (resumen, palabras clave, introducción, conclusiones, referencias, orden de secciones) |
| TABFIG | TablesFiguresAgent | tables-figures.rules.json | CUN-TF-001–CUN-TF-004 | todos | Validación de tablas y figuras (numeración, títulos, ubicación, descripción) |
| INTCIT | InTextCitationsAgent | in-text-citations.rules.json | CUN-IC-001–CUN-IC-006 | todos | Citas en texto (formato APA, año,autores, puntuación) |
| REFERENCES | ReferencesAgent | references.rules.json | CUN-REF-001–CUN-REF-006 | todos | Lista de referencias (formato, orden alfabético, completitud) |
| MATHEQUATIONS | MathEquationsAgent | math-equations.rules.json | CUN-ME-001–CUN-ME-004 | articulo_cientifico, tesis_trabajo_grado | Ecuaciones matemáticas (numeración, formato, referencias cruzadas) |
| SCIENTIFICDESIGN | ScientificDesignAgent | scientific-design.rules.json | CUN-SD-001–CUN-SD-005 | articulo_cientifico, informe_investigacion, tesis_trabajo_grado | Diseño científico (hipótesis, metodología, análisis, resultados) |
| METADATACONSISTENCY | MetadataConsistencyAgent | metadata-consistency.rules.json | CUN-MD-001–CUN-MD-003 | todos | Consistencia de metadatos (título, autor, fecha, palabras clave) |
| GLOBALFORMAT | GlobalFormatAgent | global-format.rules.json | CUN-GF-001–CUN-GF-003 | todos | Formato global del documento (fuente, tamaño, interlineado, márgenes) |

---

## Convenciones de IDs de reglas

Todas las reglas siguen el patrón: `CUN-<PREFIX>-<NNN>`

### Prefijos por agente

- **CUN-GS-xxx** → General Structure
- **CUN-TF-xxx** → Tables & Figures
- **CUN-IC-xxx** → In-Text Citations
- **CUN-REF-xxx** → References
- **CUN-ME-xxx** → Math Equations
- **CUN-SD-xxx** → Scientific Design
- **CUN-MD-xxx** → Metadata Consistency
- **CUN-GF-xxx** → Global Format

### Convención de nombre

- **CUN-** = Adaptación/alineación con Universidad CUN
- **Prefijo** = Identifica el dominio o tipo de validación
- **Sufijo numérico (NNN)** = Distingue cada regla dentro del dominio (001, 002, ...)

Ejemplo: `CUN-GS-001` = Primera regla (resumen obligatorio) del agente General Structure.

---

## Ejecución de agentes

### Orquestador de linting

El `LintOrchestrator` ejecuta todos los agentes registrados sobre el mismo documento y contexto:

1. **Ejecución secuencial del perfil**: Primero ejecuta `DocumentProfileAgent` para inferir el tipo de documento.
2. **Ejecución paralela de agentes**: Los demás agentes se ejecutan en paralelo (asincrónico) sobre el mismo documento.
3. **Agregación de resultados**: Todos los `Finding` (hallazgos) se recopilan en una lista única.
4. **Ordenamiento y resumen**: Los findings se ordenan por ubicación y se genera un resumen de estadísticas.

### Filtrado de agentes (opcional)

El cliente puede limitar qué agentes se ejecutan mediante:
- `LintRequest.options.agents` → Lista de `agent_id` a ejecutar
- Si está vacío o no especificado, se ejecutan todos los agentes registrados

Ejemplo: `{ "options": { "agents": ["GENERALSTRUCTURE", "INTCIT"] } }` ejecutará solo esos dos agentes.

---

## Integración con metadata

Desde la versión PROMPT #3 del backend, el endpoint `/lint` propaga `metadata` del `LintRequest` al `LintContext`:

```python
if request.metadata and request.context.metadata is None:
    request.context.metadata = request.metadata
```

Esto permite al agente `GlobalFormatAgent` validar propiedades como:
- `metadata.font_family` (Times New Roman, Arial)
- `metadata.font_size` (11-12pt)
- `metadata.line_spacing` (≈2.0, rango 1.8-2.2)
- `metadata.page_margins` (2.3-2.7 cm en todos los lados)

---

## Historial de cambios

- **PROMPT #2B**: Implementados 6 agentes con filtro `profile_variant`
- **PROMPT #3**: Creado `GlobalFormatAgent` con validación de formato global
- **PROMPT #4**: Documentación de registro de reglas (este archivo)
