# Guía de Contribución

¡Gracias por tu interés en contribuir a APA7 Compliance Engine Backend!

## 📋 Requisitos previos

Antes de empezar, asegúrate de:

- Tener Git instalado
- Tener Python 3.9+ instalado
- Estar familiarizado con FastAPI y pytest

## 🔧 Flujo de trabajo

### 1. Forking y clonación

```bash
# Fork el repositorio en GitHub (botón "Fork")
# Clona tu fork
git clone https://github.com/tu-usuario/apa7-compliance-engine-backend.git
cd apa7-compliance-engine-backend

# Agrega el repositorio original como upstream
git remote add upstream https://github.com/original-usuario/apa7-compliance-engine-backend.git
```

### 2. Crear una rama de feature

```bash
# Actualiza tu rama main
git fetch upstream
git checkout main
git merge upstream/main

# Crea una rama para tu feature
git checkout -b feature/nombre-descriptivo
```

### 3. Hacer cambios

- Modifica los archivos necesarios
- Asegúrate de que tu código siga los estándares (ver abajo)
- Escribe o actualiza tests para tu código

### 4. Ejecutar tests

```bash
# Instala dependencias de desarrollo (si existen)
pip install -r requirements.txt pytest pytest-cov

# Ejecuta los tests
pytest

# Verifica cobertura
pytest --cov=api tests/
```

### 5. Commit y push

```bash
git add .
git commit -m "feat: descripción clara y concisa del cambio"
git push origin feature/nombre-descriptivo
```

### 6. Pull Request

- Ve a GitHub y abre un Pull Request contra `main`
- Describe claramente qué cambios hiciste y por qué
- Enlaza cualquier issue relacionado (ej: `Closes #123`)

## 🎨 Estilo de código

### Convenciones Python

- **Formato**: Sigue [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- **Herramienta recomendada**: `black` para formateo automático
  ```bash
  pip install black
  black api/ tests/
  ```

- **Linting**: `flake8` o `pylint`
  ```bash
  pip install flake8
  flake8 api/ tests/
  ```

### Nombres de commits

Usa prefijos descriptivos:

- `feat:` Nueva funcionalidad
- `fix:` Corrección de bug
- `refactor:` Cambio de código sin alterar funcionalidad
- `docs:` Cambios en documentación
- `test:` Adición o modificación de tests
- `chore:` Cambios de configuración o dependencias

Ejemplos:
```
feat: agregar validador de referencias APA7
fix: corregir parsing de citas
docs: actualizar README con ejemplos
test: agregar tests para orchestrator
```

### Docstrings

Usa docstrings descriptivos en funciones y clases:

```python
def validate_citation(citation: str) -> bool:
    """
    Valida si una cita cumple con formato APA7.
    
    Args:
        citation: String con la cita a validar
        
    Returns:
        bool: True si es válida, False en caso contrario
    """
    pass
```

## ✅ Checklist antes de enviar PR

- [ ] Mi código sigue las convenciones de estilo (PEP 8)
- [ ] He ejecutado `pytest` y todos los tests pasan
- [ ] He agregado tests nuevos para mi funcionalidad
- [ ] He actualizado la documentación si fue necesario
- [ ] Mi rama está actualizada con `main` (sin conflictos)
- [ ] Mis commits tienen mensajes claros y descriptivos

## ❓ Preguntas o problemas

Si tienes dudas:

1. Revisa las [Issues existentes](https://github.com/tu-usuario/apa7-compliance-engine-backend/issues)
2. Abre una nueva Issue con etiqueta `question`
3. Describe tu pregunta con contexto

---

¡Gracias por contribuir! 🎉
