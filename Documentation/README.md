# Biblioteca de Clases para Modelos Semánticos de Power BI

Esta biblioteca permite cargar, manipular y guardar modelos semánticos de Power BI en formato TMDL (Tabular Model Definition Language).

## Esquema de Clases

## Direcciones de Relación vs Direcciones de Búsqueda

**IMPORTANTE:** Hay que distinguir entre dos conceptos diferentes:

### 1. Dirección de Búsqueda (parámetro del usuario)
Determina qué tablas relacionadas se incluyen en el submodelo:
- `"ManyToOne"`: Incluir tablas del lado One
- `"OneToMany"`: Incluir tablas del lado Many
- `"Both"`: Incluir tablas de ambos lados

### 2. Cardinalidad de Relación (propiedad de la relación)
Propiedad original de cada relación que se **PRESERVA INTACTA**:
- `cardinality: "manyToOne"`
- `cardinality: "oneToMany"`
- `cardinality: "oneToOne"`
- `crossFilteringBehavior: "oneDirection"`, `"bothDirections"`
- `isActive: true/false`

```python
# Ejemplo clarificador
model.create_subset_model(
    table_specs=[
        ("FactInternetSales", "ManyToOne")  # <- Dirección de BÚSQUEDA
    ],
    subset_name="SalesModel"
)

# Resultado:
# - Se incluyen DimProduct, DimCustomer, etc. (búsqueda ManyToOne)
# - Las relaciones se copian CON SUS PROPIEDADES ORIGINALES:
#   * FactInternetSales → DimProduct: cardinality="manyToOne", isActive=true
#   * FactInternetSales → DimCustomer: cardinality="manyToOne", isActive=true
```

**La dirección de búsqueda NO modifica las relaciones, solo determina qué incluir.**

