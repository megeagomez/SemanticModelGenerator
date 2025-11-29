# Platform

Representa el archivo `.platform` (JSON) con metadatos de la plataforma.

## Propiedades

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| `version` | `str` | Versión de la plataforma |
| `settings` | `dict` | Configuraciones adicionales |
| `raw_content` | `dict` | Contenido JSON original |

## Métodos

### `from_file(filepath: Path)` (class method)

Carga desde archivo JSON.

### `save_to_file(filepath: Path)`

Guarda a archivo JSON.

## Ejemplo de Archivo

```json
{
  "version": "1.0",
  "settings": {
    "autoRefresh": true
  }
}
```

## Ejemplo de Uso

```python
from models import Platform
from pathlib import Path

platform = Platform.from_file(Path(r"d:\Modelos\.platform"))
print(f"Versión: {platform.version}")
print(f"Configuración: {platform.settings}")
```

## Ver También

- [Definition](Definition.md) - Archivo relacionado
