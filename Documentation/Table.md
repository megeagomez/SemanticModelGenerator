# Table

Representa una tabla del modelo semántico con sus columnas, medidas y particiones.

## Propiedades

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| `name` | `str` | Nombre de la tabla |
| `columns` | `List[Column]` | Lista de columnas |
| `measures` | `List[Measure]` | Lista de medidas DAX |
| `partitions` | `List[Partition]` | Lista de particiones |
| `hierarchies` | `List[dict]` | Lista de jerarquías |
| `is_hidden` | `bool` | Si la tabla está oculta |
| `line_age_granularity` | `str` | Granularidad de linaje |
| `annotations` | `dict` | Anotaciones de la tabla |
| `raw_content` | `str` | Contenido original |

## Métodos

### `from_file(filepath: Path)` (class method)

Carga una tabla desde un archivo .tmdl.

```python
from pathlib import Path
from models import Table

table = Table.from_file(Path(r"d:\Modelos\Model\definition\tables\Sales.tmdl"))
```

### `save_to_file(filepath: Path)`

Guarda la tabla a un archivo .tmdl.

```python
table.save_to_file(Path(r"d:\Output\Sales.tmdl"))
```

## Métodos Estáticos de Parsing

- `_parse_columns(content: str) -> List[Column]`
- `_parse_measures(content: str) -> List[Measure]`
- `_parse_partitions(content: str) -> List[Partition]`

## Ejemplo de Formato TMDL

```tmdl
table Sales
    lineageTag: abc-123-def

    column OrderDate
        dataType: dateTime
        formatString: Short Date
        sourceColumn: OrderDate
        summarizeBy: none

    column Amount
        dataType: decimal
        formatString: #,##0.00
        sourceColumn: Amount
        summarizeBy: sum

    measure TotalSales =
        SUM(Sales[Amount])
        formatString: $#,##0.00

    partition Sales
        mode: import
        source =
            let
                Source = Sql.Database("server", "database")
            in
                Source
```

## Ejemplos de Uso

### Ejemplo 1: Explorar Tabla

```python
from pathlib import Path
from models import Table

# Cargar tabla
table = Table.from_file(Path(r"d:\Modelos\definition\tables\Sales.tmdl"))

# Información general
print(f"Tabla: {table.name}")
print(f"Oculta: {table.is_hidden}")
print(f"Columnas: {len(table.columns)}")
print(f"Medidas: {len(table.measures)}")

# Listar columnas
for col in table.columns:
    print(f"  - {col.name} ({col.data_type})")

# Listar medidas
for measure in table.measures:
    print(f"  - {measure.name}")
```

### Ejemplo 2: Modificar Propiedades

```python
# Cargar tabla
table = Table.from_file(Path(r"d:\Modelos\definition\tables\Sales.tmdl"))

# Modificar visibilidad
table.is_hidden = False

# Para modificar el contenido, necesitas editar raw_content directamente
# o reconstruir el archivo

# Guardar
table.save_to_file(Path(r"d:\Output\Sales.tmdl"))
```

## Ver También

- [Column](Column.md) - Columnas de la tabla
- [Measure](Measure.md) - Medidas DAX
- [Partition](Partition.md) - Particiones de datos
