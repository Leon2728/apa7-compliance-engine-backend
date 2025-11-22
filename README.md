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

## 🤝 Contribuciones

Por favor, lee [CONTRIBUTING.md](./CONTRIBUTING.md) para conocer nuestras directrices.

## 📄 Licencia

Este proyecto está bajo la licencia [MIT](./LICENSE).

## 📧 Contacto

Para preguntas o sugerencias, abre un issue en el repositorio.

---

**Estado**: En desarrollo 🚧
