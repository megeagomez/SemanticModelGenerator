# Column

Representa una columna de una tabla.

## Propiedades

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| `name` | `str` | Nombre de la columna |
| `data_type` | `str` | Tipo de datos (string, int64, decimal, dateTime, etc.) |
| `source_column` | `str` | Columna origen en la fuente de datos |
| `format_string` | `str` | Formato de visualización |
| `summarize_by` | `str` | Método de agregación predeterminado |
| `is_hidden` | `bool` | Si la columna está oculta |
| `raw_content` | `str` | Contenido original |

## Ejemplo TMDL

```tmdl
column ProductName
    dataType: string
    sourceColumn: ProductName
    summarizeBy: none

column UnitPrice
    dataType: decimal
    sourceColumn: UnitPrice
    formatString: $#,##0.00
    summarizeBy: sum
```

## Ejemplo de Uso

```python
# Las columnas se acceden a través de la tabla
from models import Table
from pathlib import Path

table = Table.from_file(Path(r"d:\Modelos\definition\tables\Product.tmdl"))

for column in table.columns:
    print(f"Columna: {column.name}")
    print(f"  Tipo: {column.data_type}")
    print(f"  Formato: {column.format_string}")
    print(f"  Oculta: {column.is_hidden}")
```

## Ver También

- [Table](Table.md) - Tabla contenedora
