# SemanticModel

Clase principal que representa un modelo semántico completo de Power BI.

## Propiedades

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| `base_path` | `Path` | Ruta base del modelo semántico |
| `model` | `Model` | Configuración general del modelo |
| `relationships` | `List[Relationship]` | Lista de relaciones entre tablas |
| `tables` | `List[Table]` | Lista de tablas del modelo |
| `cultures` | `List[Culture]` | Lista de configuraciones de idioma |
| `platform` | `Platform` | Metadatos de plataforma |
| `definition` | `Definition` | Definición del archivo Power BI |
| `_file_metadata` | `dict` | Metadatos para tracking de modificaciones |

## Métodos Principales

### `__init__(base_path: str)`

Constructor de la clase.

```python
semantic_model = SemanticModel(r"d:\path\to\model")
```

### `load_from_directory(directory: Path)`

Carga toda la estructura desde un directorio.

```python
model_path = Path(r"d:\Modelos\FullAdventureWorks.SemanticModel")
semantic_model.load_from_directory(model_path)
```

### `save_to_directory(output_dir: Path, only_modified: bool = False)`

Guarda la estructura a un directorio.

**Parámetros:**
- `output_dir`: Directorio de salida
- `only_modified`: Si es True, solo guarda archivos modificados

```python
# Guardar todo
semantic_model.save_to_directory(Path(r"d:\Output\Model"))

# Guardar solo modificados
semantic_model.save_to_directory(Path(r"d:\Output\Model"), only_modified=True)
```

### `create_subset_model(table_specs, subset_name, config_path=None, recursive=True, max_depth=10, table_elements=None)`

Crea un subconjunto del modelo con las tablas especificadas y sus relaciones según dirección.

**Parámetros:**
- `table_specs`: Lista de tablas (strings o tuplas)
- `subset_name`: Nombre del nuevo modelo
- `config_path`: Ruta para guardar configuración (opcional)
- `recursive`: Si True, busca relaciones recursivamente (default: True)
- `max_depth`: Profundidad máxima de recursión (default: 10)
- `table_elements`: Diccionario de especificaciones de elementos por tabla (opcional)

**IMPORTANTE - Dirección de Búsqueda vs Cardinalidad de Relaciones:**

Los parámetros `"ManyToOne"`, `"OneToMany"`, `"Both"` son **direcciones de búsqueda**, 
NO la cardinalidad de las relaciones. Las relaciones se copian con sus propiedades originales intactas:

- **Dirección de búsqueda**: Determina qué tablas relacionadas incluir
- **Cardinalidad de relación**: Se preserva del modelo original (manyToOne, oneToMany, etc.)
- **Todas las propiedades**: crossFilteringBehavior, isActive, etc. se mantienen

**Direcciones de búsqueda disponibles:**
- `"ManyToOne"`: Busca del lado Many hacia el One (ej: FactSales → DimProduct)
- `"OneToMany"`: Busca del lado One hacia el Many (ej: DimProduct → FactSales)
- `"Both"`: Busca en ambas direcciones

**Detección automática de dependencias:**

El método analiza automáticamente las expresiones DAX de las medidas para detectar referencias 
a tablas que no están explícitamente en la lista inicial. Por ejemplo:

```python
# Si FactInternetSales tiene una medida: measure 'mi media' = sum(DimProduct[ProductKey])
# DimProduct se incluirá automáticamente aunque no esté en table_specs
subset = semantic_model.create_subset_model(
    table_specs=["FactInternetSales"],
    subset_name="SalesModel"
)
# Resultado: FactInternetSales + DimProduct (detectada automáticamente)
```

**Ejemplo de uso:**

```python
# Ejemplo: Las relaciones se copian CON SUS PROPIEDADES ORIGINALES
subset = semantic_model.create_subset_model(
    table_specs=[("FactInternetSales", "ManyToOne")],  # Dirección de BÚSQUEDA
    subset_name="SalesModel"
)

# Las relaciones en subset_model mantienen:
# - cardinality: "manyToOne" (del modelo original)
# - crossFilteringBehavior: "oneDirection" (del modelo original)
# - isActive: true/false (del modelo original)
# - Todas las demás propiedades originales
```

### `load_from_config(config_path: Path, base_models_dir: Path)` (class method)

Carga un modelo desde un archivo de configuración.

```python
model = SemanticModel.load_from_config(
    config_path=Path(r"d:\Config\sales_config.json"),
    base_models_dir=Path(r"d:\Modelos")
)
```

## Métodos Privados

### `_find_related_tables_by_direction(table_name: str, direction: str) -> Set[str]`

Encuentra tablas relacionadas según la dirección especificada.

**Direcciones:**
- `"ManyToOne"`: Tablas del lado One de relaciones Many-to-One
- `"OneToMany"`: Tablas del lado Many de relaciones Many-to-One
- `"Both"`: Ambas direcciones

**Ejemplo:**
```python
# Internamente usado por create_subset_model
related = model._find_related_tables_by_direction("Internet Sales", "ManyToOne")
# Retorna: {'DimCustomer', 'DimProduct', 'DimDate', ...}
```

### `_find_related_tables_recursive(...)`

Busca tablas relacionadas de forma recursiva hasta alcanzar `max_depth`.

**Parámetros:**
- `initial_specs`: Especificaciones iniciales de tablas
- `tables_to_include`: Conjunto que se va llenando con tablas encontradas
- `table_configs`: Configuración de dirección por tabla
- `current_depth`: Profundidad actual de recursión
- `max_depth`: Profundidad máxima permitida

### `_find_directly_related_tables(table_name: str) -> Set[str]`

**[DEPRECATED]** Encuentra tablas directamente relacionadas sin considerar dirección.
Usar `_find_related_tables_by_direction` en su lugar.

### `_relationship_involves_tables(relationship: Relationship, table_names: Set[str]) -> bool`

Verifica si una relación involucra solo tablas del conjunto especificado.

### `_rebuild_relationships_content(relationships: List[Relationship]) -> str`

Reconstruye el contenido del archivo relationships.tmdl.

### `_get_table_names() -> Set[str]`

Obtiene el conjunto de nombres de todas las tablas del modelo.

## Ejemplos de Uso Detallados

### Ejemplo 1: Carga y Exploración

```python
from pathlib import Path
from models import SemanticModel

# Cargar modelo
model = SemanticModel(r"d:\Modelos\FullAdventureWorks.SemanticModel")
model.load_from_directory(Path(r"d:\Modelos\FullAdventureWorks.SemanticModel"))

# Explorar contenido
print(f"Total de tablas: {len(model.tables)}")
print(f"Total de relaciones: {len(model.relationships)}")

# Listar tablas
for table in model.tables:
    print(f"- {table.name}: {len(table.columns)} columnas, {len(table.measures)} medidas")
```

### Ejemplo 2: Modelo centrado en hechos (solo dimensiones)

```python
# Internet Sales con todas sus dimensiones (recursive ManyToOne)
sales_model = model.create_subset_model(
    table_specs=["Internet Sales"],
    subset_name="InternetSalesDimensions.SemanticModel",
    recursive=True,
    max_depth=10
)

# Guardar
sales_model.save_to_directory(Path(r"d:\Modelos\InternetSalesDimensions.SemanticModel"))

# Resultado: Internet Sales + DimCustomer + DimProduct + DimDate + 
#            DimCurrency + DimPromotion + DimSalesTerritory + 
#            DimProductSubcategory + DimProductCategory + DimGeography
```

### Ejemplo 3: Modelo centrado en dimensión (incluye hechos)

```python
# DimProduct con todos los hechos que lo usan
product_model = model.create_subset_model(
    table_specs=[("DimProduct", "OneToMany")],
    subset_name="ProductAnalysis.SemanticModel",
    recursive=True,
    max_depth=5
)

product_model.save_to_directory(Path(r"d:\Modelos\ProductAnalysis.SemanticModel"))

# Resultado: DimProduct + Internet Sales + FactResellerSales + 
#            FactProductInventory + todas sus dimensiones relacionadas
```

### Ejemplo 4: Modelo complejo con múltiples direcciones

```python
complex_model = model.create_subset_model(
    table_specs=[
        ("Internet Sales", "ManyToOne"),  # Solo dimensiones de Internet Sales
        ("DimProduct", "Both"),            # Dimensiones de Product Y hechos que usan Product
        ("DimDate", "OneToMany")          # Todos los hechos que usan Date
    ],
    subset_name="ComplexSalesModel.SemanticModel",
    recursive=True,
    max_depth=3  # Limitar recursión a 3 niveles
)

complex_model.save_to_directory(Path(r"d:\Modelos\ComplexSalesModel.SemanticModel"))

print(f"Tablas incluidas: {len(complex_model.tables)}")
for table in sorted(complex_model.tables, key=lambda t: t.name):
    print(f"  - {table.name}")
```

### Ejemplo 5: Control de profundidad

```python
# Un solo nivel de relaciones
shallow_model = model.create_subset_model(
    table_specs=["Internet Sales"],
    subset_name="ShallowModel.SemanticModel",
    recursive=False  # Solo tablas directamente relacionadas
)

print(f"Modelo superficial: {len(shallow_model.tables)} tablas")
# Resultado: Internet Sales + solo sus dimensiones directas

# Múltiples niveles controlados
deep_model = model.create_subset_model(
    table_specs=["Internet Sales"],
    subset_name="DeepModel.SemanticModel",
    recursive=True,
    max_depth=2  # Máximo 2 niveles de profundidad
)

print(f"Modelo profundo (2 niveles): {len(deep_model.tables)} tablas")
# Resultado: Internet Sales + dimensiones + dimensiones de dimensiones (2 niveles)
```

### Ejemplo 6: Modificación y Guardado Selectivo

```python
# Modificar una tabla
for table in model.tables:
    if table.name == "Internet Sales":
        table.is_hidden = False
        model._file_metadata['tables'][table.name]['modified'] = True

# Guardar solo lo modificado
model.save_to_directory(
    Path(r"d:\Modelos\Modified.SemanticModel"),
    only_modified=True
)
```

### Ejemplo 7: Trabajar con Relaciones

```python
# Listar todas las relaciones de una tabla
table_name = "Internet Sales"
related_tables = model._find_related_tables_by_direction(table_name, "ManyToOne")

print(f"Dimensiones relacionadas con {table_name}:")
for rel_table in related_tables:
    print(f"  - {rel_table}")

# Analizar cardinalidad de relaciones
for rel in model.relationships:
    if rel.from_table == table_name or rel.to_table == table_name:
        print(f"{rel.from_table}[{rel.from_column}] -> {rel.to_table}[{rel.to_column}]")
        print(f"  Cardinalidad: {rel.cardinality or 'manyToOne (default)'}")
        print(f"  Activa: {rel.is_active}")
```

## Archivo de Configuración

El archivo JSON generado incluye información completa sobre la configuración del submodelo:

```json
{
  "name": "SalesModel.SemanticModel",
  "base_model": "FullAdventureWorks.SemanticModel",
  "initial_tables": [
    {
      "name": "Internet Sales",
      "direction": "ManyToOne"
    },
    {
      "name": "DimProduct",
      "direction": "Both"
    }
  ],
  "included_tables": [
    "Internet Sales",
    "DimProduct",
    "DimCustomer",
    "DimDate",
    "DimCurrency",
    "DimProductSubcategory",
    "DimProductCategory",
    "FactResellerSales"
  ],
  "table_configs": {
    "Internet Sales": "ManyToOne",
    "DimProduct": "Both",
    "DimCustomer": "ManyToOne",
    "DimDate": "ManyToOne",
    "DimCurrency": "ManyToOne",
    "DimProductSubcategory": "ManyToOne",
    "DimProductCategory": "ManyToOne",
    "FactResellerSales": "ManyToOne"
  },
  "total_tables": 8,
  "recursive": true,
  "max_depth": 10,
  "creation_date": null
}
```

## Comportamiento de Direcciones de Búsqueda

### ManyToOne (Búsqueda predeterminada)
Desde una tabla de hechos hacia sus dimensiones:

```python
# Desde Internet Sales (hechos) hacia DimProduct y DimCustomer (dimensiones)
model._find_related_tables_by_direction("Internet Sales", "ManyToOne")
# Retorna: {'DimProduct', 'DimCustomer', ...}
```

### OneToMany
Desde una dimensión hacia las tablas de hechos relacionadas:

```python
# Desde DimProduct hacia todas las tablas de hechos relacionadas
model._find_related_tables_by_direction("DimProduct", "OneToMany")
# Retorna: {'Internet Sales', 'FactResellerSales', ...}
```

### Both
Busca en ambas direcciones:

```python
# Buscar relaciones en ambas direcciones para DimProduct
model._find_related_tables_by_direction("DimProduct", "Both")
# Retorna: {'Internet Sales', 'FactResellerSales', 'DimCustomer', ...}
```

### Ejemplo de Uso de Filtrado de Elementos

```python
from models import TableElementSpec

# Especificar elementos a incluir/excluir
element_specs = {
    "Internet Sales": TableElementSpec(
        columns=["SalesAmount", "OrderQuantity"],
        measures=["Total Sales"],
        mode='include'  # Incluir solo estos elementos
    ),
    "DimCustomer": TableElementSpec(
        columns=["InternalColumn"],
        mode='exclude'  # Excluir este elemento
    )
}

# Crear modelo con filtrado de elementos
filtered_model = model.create_subset_model(
    table_specs=["Internet Sales", "DimCustomer"],
    subset_name="FilteredSalesModel",
    table_elements=element_specs
)

# Guardar modelo filtrado
filtered_model.save_to_directory(Path(r"d:\Modelos\FilteredSalesModel"))
```
