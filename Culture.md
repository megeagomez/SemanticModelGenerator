# Culture

Representa una configuración de idioma/cultura del modelo.

## Propiedades

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| `name` | `str` | Código de cultura (ej: "es-ES", "en-US") |
| `linguistic_metadata` | `str` | Metadatos lingüísticos |
| `raw_content` | `str` | Contenido original |

## Métodos

### `from_file(filepath: Path)` (class method)

Carga una cultura desde un archivo .tmdl.

### `save_to_file(filepath: Path)`

Guarda la cultura a un archivo .tmdl.

## Ejemplo de Uso

```python
from models import Culture
from pathlib import Path

culture = Culture.from_file(Path(r"d:\Modelos\definition\cultures\es-ES.tmdl"))
print(f"Cultura: {culture.name}")
```

## Ver También

- [SemanticModel](SemanticModel.md) - Clase contenedora
