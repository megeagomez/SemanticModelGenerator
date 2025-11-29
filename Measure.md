# Measure

Representa una medida DAX en una tabla.

## Propiedades

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| `name` | `str` | Nombre de la medida |
| `expression` | `str` | Expresión DAX |
| `format_string` | `str` | Formato de visualización |
| `is_hidden` | `bool` | Si la medida está oculta |
| `raw_content` | `str` | Contenido original |

## Ejemplo TMDL

```tmdl
measure TotalSales =
    SUM(Sales[Amount])
    formatString: $#,##0.00

measure AverageSalesPerCustomer =
    DIVIDE(
        [TotalSales],
        DISTINCTCOUNT(Sales[CustomerKey])
    )
    formatString: $#,##0.00
```

## Ejemplo de Uso

```python
from models import Table
from pathlib import Path

table = Table.from_file(Path(r"d:\Modelos\definition\tables\Sales.tmdl"))

for measure in table.measures:
    print(f"Medida: {measure.name}")
    print(f"  Formato: {measure.format_string}")
    print(f"  Expresión:\n{measure.expression}")
```

## Ver También

- [Table](Table.md) - Tabla contenedora
