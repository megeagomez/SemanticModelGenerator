# Definition

Representa el archivo `definition.pbism` (JSON) con la definición del modelo Power BI.

## Propiedades

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| `version` | `str` | Versión del formato |
| `metadata_version` | `str` | Versión de metadatos |
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
  "metadataVersion": "3.0"
}
```

## Ejemplo de Uso

```python
from models import Definition
from pathlib import Path

definition = Definition.from_file(Path(r"d:\Modelos\definition.pbism"))
print(f"Versión: {definition.version}")
print(f"Metadata Version: {definition.metadata_version}")
```

## Ver También

- [Platform](Platform.md) - Archivo relacionado
