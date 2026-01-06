# Changelog - Generación de Modelos Mínimos Power BI

## [2026-01-06] - Filtrado Selectivo de Relaciones y Columnas

### 🎯 Nuevas Funcionalidades

#### 1. Filtrado Selectivo de Relaciones
Los modelos mínimos (subset models) ahora incluyen **solo las relaciones necesarias** entre las tablas que se usan realmente.

**Impacto:**
- ✅ Reducción típica: 60-80% de relaciones eliminadas en submodelos
- ✅ Archivos más pequeños y modelos más limpios
- ✅ Mejor rendimiento en Power BI Desktop

**Ejemplo:**
```python
subset = model.create_subset_model(
    table_specs=["FactInternetSales"],
    subset_name="MinimalSales",
    recursive=False
)
# Resultado: Solo 1 relación (FactInternetSales -> DimProduct)
# vs 38 relaciones del modelo original
```

#### 2. Detección Automática de Dependencias DAX
El sistema analiza automáticamente las expresiones DAX de las medidas para detectar:
- Tablas referenciadas externamente: `sum(DimProduct[ProductKey])`
- Columnas usadas dentro de la misma tabla: `sum(FactInternetSales[OrderQuantity])`

**Beneficios:**
- Auto-inclusión de tablas necesarias aunque no estén especificadas
- Filtrado inteligente de columnas por uso real
- Especificaciones generadas automáticamente

#### 3. Filtrado de Columnas por Uso Real
Las tablas en submodelos incluyen **solo las columnas usadas** en:
- Medidas DAX
- Relaciones activas
- Referencias entre tablas

**Ejemplo:**
```
FactInternetSales: 26 → 2 columnas (ProductKey + OrderQuantity)
DimProduct: 35 → 1 columna (ProductKey)
```

### 🐛 Correcciones

#### Fix: Power BI Desktop no abre reportes vacíos
**Problema:** El campo `"pages": []` en `report.json` causaba error de esquema.

**Solución:** El archivo `report.json` ya no incluye la propiedad `pages` cuando está vacía.

**Archivos modificados:**
- `mcp_server.py` (método `_copy_and_merge_report_pages`)

### 🔧 Cambios Técnicos

#### Archivo: `models/semantic_model.py`

**Nuevos métodos:**
- `_extract_columns_from_measures_in_tables()`: Analiza columnas usadas en medidas de tablas iniciales
- Mejorado `_extract_table_references_from_measures()`: Captura referencias externas a otras tablas

**Método actualizado: `create_subset_model()`**
- Reorganizado flujo de operaciones para análisis correcto de dependencias
- Definición correcta de `final_tables` según modo `recursive`
- Filtrado de relaciones usando `final_tables` (solo tablas realmente usadas)
- Auto-creación de `TableElementSpec` para tablas detectadas

**Lógica de `final_tables`:**
```python
if not recursive:
    # Solo tablas iniciales + detectadas en medidas
    final_tables = initial_tables_only.copy()
else:
    # Todas las tablas buscadas recursivamente + medidas
    final_tables = tables_for_relationships.copy()
```

### 📊 Resultados de Tests

**Test 1: Submodelo con tabla única (recursive=False)**
- Entrada: `FactInternetSales`
- Salida: 2 tablas, 1 relación
- ✅ DimProduct detectada automáticamente por medida "mi media"

**Test 2: Submodelo con dos tablas (recursive=False)**
- Entrada: `FactInternetSales`, `DimProduct`
- Salida: 2 tablas, 1 relación
- ✅ Solo relación necesaria entre las dos

**Test 3: Submodelo recursivo (recursive=True, max_depth=3)**
- Entrada: `FactInternetSales`
- Salida: 10 tablas, 12 relaciones
- ✅ 68% menos relaciones que modelo original (38 → 12)
- ✅ Tablas encontradas en 2 niveles de profundidad

### 📝 Archivos de Test Incluidos

1. `scripts/test_measure_dependencies.py` - Verifica detección de dependencias DAX
2. `scripts/test_empty_pages.py` - Verifica esquema correcto de report.json
3. `scripts/test_debug_filtering.py` - Verifica filtrado detallado de columnas
4. `scripts/check_measures.py` - Analiza columnas usadas por medida
5. `test_relationships_filtering.py` - Verifica filtrado selectivo de relaciones
6. `test_recursive_simple.py` - Verifica búsqueda recursiva de tablas

### 📚 Documentación

- `CAMBIOS_MODELOS_MINIMOS.md` - Documentación detallada de problemas y soluciones
- `SOLUCION_FILTRADO_RELACIONES.md` - Explicación técnica del filtrado de relaciones
- `SemanticModel.md` - Actualizada con nuevas capacidades

### 🚀 Próximos Pasos (Opcionales)

1. Análisis transitivo de dependencias DAX
2. Incluir referencias de indicadores y filtros de reportes
3. Compresión adicional: eliminar jerarquías no usadas
4. Validación de integridad post-filtrado

---

## Uso del Sistema

### Crear Modelo Mínimo con Filtrado Inteligente

```python
from models.semantic_model import SemanticModel

# Cargar modelo original
model = SemanticModel("Modelos/FullAdventureWorks.SemanticModel")
model.load_from_directory(model.base_path)

# Crear subset con filtrado automático
subset = model.create_subset_model(
    table_specs=["FactInternetSales"],
    subset_name="MinimalSales",
    recursive=False
)

# Guardar
subset.save_to_directory(Path("Modelos/MinimalSales.SemanticModel"))
```

### Características del Subset Generado

✅ **Solo tablas usadas** (directas + indirectas por medidas)  
✅ **Solo relaciones necesarias** (entre tablas incluidas)  
✅ **Solo columnas usadas** (en medidas + relaciones)  
✅ **Todas las medidas** preservadas  
✅ **Propiedades originales** mantenidas

---

**Fecha:** 2026-01-06  
**Autor:** AI Coding Assistant  
**Versión:** 1.0.0
