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

- ## 🤖 Reglas LLM Semánticas (llm_semantic)

Esta versión incluye soporte para reglas que utilizan modelos LLM (Large Language Models) para análisis semántico avanzado de documentos.

### ¿Qué es checkType="llm_semantic"?

`llm_semantic` es un tipo de regla que delega la evaluación de cumplimiento a un modelo LLM, permitiendo análisis más profundos y contextuales que las reglas basadas en patrones regex.

### Configuración de llmConfig

Cada regla LLM incluye un objeto `llmConfig` que controla su comportamiento:

- `enabled`: Habilita/deshabilita la evaluación LLM
- `mode`: Rol del LLM (validator, classifier, suggester, generator)
- `max_chars`: Máximo de caracteres a procesar
- `forbidden_behaviors`: Restricciones que el LLM debe respetar
- `allowed_suggestion_types`: Tipos de sugerencias permitidas
- `output_format`: Formato esperado de respuesta LLM

### Optionalidad del LLM - 100% Backward Compatible

El sistema es completamente funcional sin LLM configurado:

- Si `LLM_ENABLED=false`: Las reglas llm_semantic se omiten silenciosamente (sin errores)
- Si no hay cliente LLM disponible: Las reglas llm_semantic no se ejecutan
- El resto del motor sigue funcionando normalmente
- **Sin LLM, el comportamiento es idéntico a versiones anteriores**



## 🤝 Contribuciones

Por favor, lee [CONTRIBUTING.md](./CONTRIBUTING.md) para conocer nuestras directrices.

## 📄 Licencia

Este proyecto está bajo la licencia [MIT](./LICENSE).

## 📧 Contacto

Para preguntas o sugerencias, abre un issue en el repositorio.

---

**Estado**: En desarrollo 🚧
