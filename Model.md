# Model

Representa el archivo `model.tmdl` que contiene la configuración general del modelo semántico.

## Propiedades

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| `name` | `str` | Nombre del modelo |
| `culture` | `str` | Cultura predeterminada (ej: "en-US") |
| `data_access_options` | `dict` | Opciones de acceso a datos |
| `default_power_bi_data_source_version` | `str` | Versión de fuente de datos |
| `source_query_culture` | `str` | Cultura para consultas |
| `annotations` | `dict` | Anotaciones del modelo |
| `raw_content` | `str` | Contenido original del archivo |

## Métodos

### `from_file(filepath: Path)` (class method)

Carga el modelo desde un archivo .tmdl.

```python
from pathlib import Path
from models import Model

model = Model.from_file(Path(r"d:\Modelos\Model\definition\model.tmdl"))
```

### `save_to_file(filepath: Path)`

Guarda el modelo a un archivo .tmdl.

```python
model.save_to_file(Path(r"d:\Output\model.tmdl"))
```

## Ejemplo de Archivo TMDL

```tmdl
model Model
    culture: en-US
    defaultPowerBIDataSourceVersion: powerBI_V3
    sourceQueryCulture: en-US

    dataAccessOptions
        legacyRedirects
        returnErrorValuesAsNull

    annotation PBI_QueryOrder = ["Sales", "Product"]
    annotation __PBI_TimeIntelligenceEnabled = 1
```

## Ejemplos de Uso

### Ejemplo 1: Leer Configuración

```python
from pathlib import Path
from models import Model

# Cargar modelo
model = Model.from_file(Path(r"d:\Modelos\Model\definition\model.tmdl"))

# Acceder a propiedades
print(f"Nombre: {model.name}")
print(f"Cultura: {model.culture}")
print(f"Versión: {model.default_power_bi_data_source_version}")

# Acceder a anotaciones
for key, value in model.annotations.items():
    print(f"Anotación {key}: {value}")
```

### Ejemplo 2: Modificar y Guardar

```python
# Cargar
model = Model.from_file(Path(r"d:\Modelos\Model\definition\model.tmdl"))

# Modificar cultura
model.culture = "es-ES"
model.source_query_culture = "es-ES"

# Nota: Para modificar el raw_content, necesitas manipular el texto directamente
# o usar el TmdlParser para reconstruir

# Guardar
model.save_to_file(Path(r"d:\Output\model.tmdl"))
```

## Ver También

- [SemanticModel](SemanticModel.md) - Clase contenedora
- [TmdlParser](TmdlParser.md) - Parser para formato TMDL
