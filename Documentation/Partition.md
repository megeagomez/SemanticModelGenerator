# Partition

Representa una partición de datos de una tabla.

## Propiedades

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| `name` | `str` | Nombre de la partición |
| `mode` | `str` | Modo (import, directQuery, etc.) |
| `source` | `dict` | Configuración de la fuente de datos |
| `raw_content` | `str` | Contenido original |

## Ejemplo TMDL

```tmdl
partition Sales
    mode: import
    source =
        let
            Source = Sql.Database("localhost", "AdventureWorks"),
            Sales = Source{[Schema="Sales",Item="SalesOrderHeader"]}[Data]
        in
            Sales
```

## Ejemplo de Uso

```python
from models import Table
from pathlib import Path

table = Table.from_file(Path(r"d:\Modelos\definition\tables\Sales.tmdl"))

for partition in table.partitions:
    print(f"Partición: {partition.name}")
    print(f"  Modo: {partition.mode}")
```

## Ver También

- [Table](Table.md) - Tabla contenedora
