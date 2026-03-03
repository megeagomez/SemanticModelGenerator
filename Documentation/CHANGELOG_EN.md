# Changelog - Power BI Minimal Models Generation

**[Español](CHANGELOG.md) | English**

---

## [2026-01-06] - Selective Filtering of Relationships and Columns

### 🎯 New Features

#### 1. Selective Relationship Filtering
Minimal models (subset models) now include **only necessary relationships** between tables that are actually used.

**Impact:**
- ✅ Typical reduction: 60-80% of relationships removed in submodels
- ✅ Smaller files and cleaner models
- ✅ Better performance in Power BI Desktop

**Example:**
```python
subset = model.create_subset_model(
    table_specs=["FactInternetSales"],
    subset_name="MinimalSales",
    recursive=False
)
# Result: Only 1 relationship (FactInternetSales -> DimProduct)
# vs 38 relationships in original model
```

#### 2. Automatic DAX Dependency Detection
The system automatically analyzes DAX expressions in measures to detect:
- Externally referenced tables: `sum(DimProduct[ProductKey])`
- Columns used within the same table: `sum(FactInternetSales[OrderQuantity])`

**Benefits:**
- Auto-inclusion of necessary tables even if not specified
- Intelligent column filtering by actual usage
- Automatically generated specifications

#### 3. Column Filtering by Actual Usage
Tables in submodels include **only columns used** in:
- DAX measures
- Active relationships
- Cross-table references

**Example:**
```
FactInternetSales: 26 → 2 columns (ProductKey + OrderQuantity)
DimProduct: 35 → 1 column (ProductKey)
```

### 🐛 Bug Fixes

#### Fix: Power BI Desktop doesn't open empty reports
**Problem:** The `"pages": []` field in `report.json` caused a schema error.

**Solution:** The `report.json` file no longer includes the `pages` property when empty.

**Modified files:**
- `mcp_server.py` (method `_copy_and_merge_report_pages`)

### 🔧 Technical Changes

#### File: `models/semantic_model.py`

**New methods:**
- `_extract_columns_from_measures_in_tables()`: Analyzes columns used in measures of initial tables
- Improved `_extract_table_references_from_measures()`: Captures external references to other tables

**Updated method: `create_subset_model()`**
- Reorganized operation flow for correct dependency analysis
- Correct definition of `final_tables` according to `recursive` mode
- Relationship filtering using `final_tables` (only actually used tables)
- Auto-creation of `TableElementSpec` for detected tables

**`final_tables` logic:**
```python
if not recursive:
    # Only initial tables + detected in measures
    final_tables = initial_tables_only.copy()
else:
    # All recursively searched tables + measures
    final_tables = tables_for_relationships.copy()
```

### 📊 Test Results

**Test 1: Submodel with single table (recursive=False)**
- Input: `FactInternetSales`
- Output: 2 tables, 1 relationship
- ✅ DimProduct automatically detected by measure "mi media"

**Test 2: Submodel with two tables (recursive=False)**
- Input: `FactInternetSales`, `DimProduct`
- Output: 2 tables, 1 relationship
- ✅ Only necessary relationship between the two

**Test 3: Recursive submodel (recursive=True, max_depth=3)**
- Input: `FactInternetSales`
- Output: 10 tables, 12 relationships
- ✅ 68% fewer relationships than original model (38 → 12)
- ✅ Tables found at 2 depth levels

### 📝 Included Test Files

1. `scripts/test_measure_dependencies.py` - Verifies DAX dependency detection
2. `scripts/test_empty_pages.py` - Verifies correct report.json schema
3. `scripts/test_debug_filtering.py` - Verifies detailed column filtering
4. `scripts/check_measures.py` - Analyzes columns used per measure
5. `test_relationships_filtering.py` - Verifies selective relationship filtering
6. `test_recursive_simple.py` - Verifies recursive table search

### 📚 Documentation

- `CHANGELOG.md` / `CHANGELOG_EN.md` - Summary of changes and usage
- `CAMBIOS_MODELOS_MINIMOS.md` / `MINIMAL_MODELS_CHANGES_EN.md` - Detailed documentation of problems and solutions
- `SOLUCION_FILTRADO_RELACIONES.md` / `RELATIONSHIPS_FILTERING_SOLUTION_EN.md` - Technical explanation of relationship filtering
- `SemanticModel.md` - Updated with new capabilities

### 🚀 Next Steps (Optional)

1. Transitive analysis of DAX dependencies
2. Include references from report indicators and filters
3. Additional compression: remove unused hierarchies
4. Post-filtering integrity validation

---

## System Usage

### Create Minimal Model with Intelligent Filtering

```python
from models.semantic_model import SemanticModel

# Load original model
model = SemanticModel("Modelos/FullAdventureWorks.SemanticModel")
model.load_from_directory(model.base_path)

# Create subset with automatic filtering
subset = model.create_subset_model(
    table_specs=["FactInternetSales"],
    subset_name="MinimalSales",
    recursive=False
)

# Save
subset.save_to_directory(Path("Modelos/MinimalSales.SemanticModel"))
```

### Generated Subset Features

✅ **Only used tables** (direct + indirect through measures)  
✅ **Only necessary relationships** (between included tables)  
✅ **Only used columns** (in measures + relationships)  
✅ **All measures** preserved  
✅ **Original properties** maintained

---

**Date:** 2026-01-06  
**Author:** AI Coding Assistant  
**Version:** 1.0.0
