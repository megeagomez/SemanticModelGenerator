# Relationship

Representa una relación entre tablas en el modelo semántico.

## Propiedades

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| `name` | `str` | Nombre de la relación (UUID o identificador) |
| `from_table` | `str` | Tabla origen (extraída de fromColumn) |
| `from_column` | `str` | Columna origen (extraída de fromColumn) |
| `to_table` | `str` | Tabla destino (extraída de toColumn) |
| `to_column` | `str` | Columna destino (extraída de toColumn) |
| `cross_filtering_behavior` | `str` | Comportamiento de filtro cruzado |
| `security_filtering_behavior` | `str` | Comportamiento de filtro de seguridad |
| `cardinality` | `str` | Cardinalidad (OneToMany, ManyToOne, etc.) |
| `is_active` | `bool` | Si la relación está activa |
| `raw_content` | `str` | Contenido original |

## Formato del Archivo relationships.tmdl

El archivo `relationships.tmdl` usa un formato especial donde `fromColumn` y `toColumn` incluyen tanto la tabla como la columna en formato `tabla.columna`:

```tmdl
relationship 7d64cdb9-fad5-45f2-8794-9366f149158c
	fromColumn: 'Internet Sales'.CurrencyKey
	toColumn: DimCurrency.CurrencyKey

	annotation PBI_IsFromSource = FS

relationship c79a882a-c4cb-4d1e-94d2-307e6452690b
	fromColumn: 'Internet Sales'.CustomerKey
	toColumn: DimCustomer.CustomerKey
```

**Notas importantes:**
- Si el nombre de tabla contiene espacios o caracteres especiales, se encierra entre comillas simples: `'Internet Sales'`
- Si el nombre de columna contiene espacios, también se encierra: `'Due Date Key'`
- Tablas y columnas sin espacios no requieren comillas: `DimCurrency.CurrencyKey`

## Métodos

### `from_file(filepath: Path)` (class method)

Carga una relación desde un archivo .tmdl.

### `parse_all_from_content(content: str)` (class method)

Parsea todas las relaciones desde el contenido de relationships.tmdl.

```python
with open("relationships.tmdl", "r", encoding="utf-8") as f:
    content = f.read()

relationships = Relationship.parse_all_from_content(content)
```

### `_parse_table_column(combined_value: str)` (static method)

Parsea el formato combinado tabla.columna y extrae ambos componentes.

**Ejemplos:**
- `'Internet Sales'.'Due Date Key'` → `('Internet Sales', 'Due Date Key')`
- `DimCurrency.CurrencyKey` → `('DimCurrency', 'CurrencyKey')`
- `'Table Name'.ColumnName` → `('Table Name', 'ColumnName')`

### `save_to_file(filepath: Path)`

Guarda la relación a un archivo.

## Ejemplos de Uso

### Ejemplo 1: Analizar Relaciones

```python
from models import SemanticModel
from pathlib import Path

model = SemanticModel(r"d:\Modelos\Model")
model.load_from_directory(Path(r"d:\Modelos\Model"))

# Analizar todas las relaciones
for rel in model.relationships:
    print(f"Relación: {rel.name}")
    print(f"  De: {rel.from_table}[{rel.from_column}]")
    print(f"  A: {rel.to_table}[{rel.to_column}]")
    print(f"  Cardinalidad: {rel.cardinality}")
    print(f"  Activa: {rel.is_active}")
    print()
```

### Ejemplo 2: Filtrar Relaciones por Tabla

```python
table_name = "Internet Sales"
related = [
    rel for rel in model.relationships
    if rel.from_table == table_name or rel.to_table == table_name
]

print(f"Relaciones que involucran '{table_name}': {len(related)}")
for rel in related:
    if rel.from_table == table_name:
        print(f"  -> {rel.to_table} (por columna {rel.from_column})")
    else:
        print(f"  <- {rel.from_table} (por columna {rel.to_column})")
```

### Ejemplo 3: Relaciones con Nombres con Espacios

```python
# Las relaciones manejan correctamente nombres con espacios
for rel in model.relationships:
    # Tablas con espacios como 'Internet Sales' se parsean correctamente
    if ' ' in rel.from_table or ' ' in rel.to_table:
        print(f"Relación con tabla de nombre compuesto:")
        print(f"  {rel.from_table} -> {rel.to_table}")
```

## Ver También

- [SemanticModel](SemanticModel.md) - Clase contenedora
- [Table](Table.md) - Tablas relacionadas
- [TmdlParser](TmdlParser.md) - Parser de formato TMDL
