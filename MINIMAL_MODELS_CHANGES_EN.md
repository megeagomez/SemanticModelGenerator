# Changes Made - Improvements in Minimal Models Generation

**[Español](CAMBIOS_MODELOS_MINIMOS.md) | English**

---

## Problem 1: report.json contains empty `"pages": []`
**Symptom**: Power BI Desktop doesn't open empty reports because the `"pages": []` field must not be present in `report.json` if empty.

**Solution**: Modified method `_copy_and_merge_report_pages()` in [mcp_server.py](mcp_server.py#L832-L897)
- Removed line that initialized `target_data["pages"] = []`
- Added logic at the end to remove the `"pages"` key if empty
- Now the file is saved without the property when there are no pages

**Impact**: Empty reports now open correctly in Power BI Desktop

---

## Problem 2: All columns are included without filtering
**Symptom**: When creating a minimal model, all columns from all tables were included without filtering by usage.

**Root cause**: Column filtering was only applied to tables detected in external references (e.g., DimProduct referenced by measure in FactInternetSales), but NOT applied to:
1. Initial tables specified in the subset (e.g., FactInternetSales)
2. Measures defined in those tables were not analyzed

**Solution**: Three coordinated changes:

### 2.1 New method: `_extract_columns_from_measures_in_tables()`
Added in [semantic_model.py](models/semantic_model.py#L747-L790):
- Analyzes MEASURES of initial tables
- Searches for references to columns of the SAME table: `FactInternetSales[OrderQuantity]`
- Extracts only columns used in DAX expressions
- Returns dictionary `{table: {column1, column2, ...}}`

### 2.2 Improved method: `_extract_table_references_from_measures()`
Already existed, now captures references to OTHER tables:
- Searches for `ExternalTable[Column]` in measures
- Returns dictionary with referenced external columns

### 2.3 Updated method: `create_subset_model()`
Changes in [semantic_model.py](models/semantic_model.py#L280-L325):
- Calls `_extract_columns_from_measures_in_tables()` for initial tables BEFORE processing relationships
- Auto-creates `TableElementSpec` with specific columns for each table
- Applies specifications during element filtering

**Impact**:
```
Final subset result:
- FactInternetSales: 26 → 2 columns (ProductKey for relationship + OrderQuantity for measure)
- DimProduct: 35 → 1 column (ProductKey for measure and relationship)
```

---

## Problem 3: All relationships are included regardless of usage
**Symptom**: Subset models included ALL relationships between existing tables, even those not connecting actually used tables.

**Root cause**: The code was using `tables_for_relationships` to filter relationships, which included:
1. Specified initial tables
2. Tables found in recursive search
3. Tables detected in DAX measure references

However, when `recursive=False`, all related tables from the original model were being included, not just initial tables.

**Solution**: Reorganization of `create_subset_model()` logic

### 3.1 Correct definition of `final_tables`
Added in [semantic_model.py](models/semantic_model.py#L304-L320):
```python
# When recursive=False: initial tables + measures
# When recursive=True: ALL searched tables (initial + related + measures)
if not recursive:
    # recursive=False: only initial tables + measures
    final_tables = initial_tables_only.copy()
else:
    # recursive=True: all tables found in recursive search
    final_tables = tables_for_relationships.copy()
```

### 3.2 Selective relationship filtering
Updated in [semantic_model.py](models/semantic_model.py#L345-L350):
```python
# NOW: Filter relationships to ONLY include where BOTH tables are in final_tables
subset_relationships = []
for rel in self.relationships:
    if self._relationship_involves_tables(rel, final_tables):
        subset_relationships.append(rel)
```

**Impact**:
```
Test results:
- Original model: 38 relationships between 25 tables
- Subset (recursive=False): 1 relationship (only necessary)
- Subset (recursive=True, depth=3): 12 relationships (68% reduction)
```

---

## Complete Example

```python
subset = model.create_subset_model(
    table_specs=[("FactInternetSales", "ManyToOne")],
    subset_name="MinimalSales"
)
```

**Process output:**
```
Columns used in measures of initial tables:
  FactInternetSales:
    Referenced columns: OrderQuantity

Tables referenced in DAX measures:
  + Adding 'DimProduct' (referenced in DAX expressions)
    Columns used: ProductKey
```

**Final result:**
- ✅ FactInternetSales: 26 → 2 columns (ProductKey + OrderQuantity)
- ✅ DimProduct: 35 → 1 column (ProductKey)  
- ✅ All measures included (OrderQty, mi media)
- ✅ Only necessary relationship preserved

---

## Modified Files

1. **[mcp_server.py](mcp_server.py)**
   - Lines 832-897: Method `_copy_and_merge_report_pages()`
   - Change: Empty `"pages"` removal logic

2. **[models/semantic_model.py](models/semantic_model.py)**
   - Lines 280-325: Updated method `create_subset_model()`
   - Lines 747-790: New method `_extract_columns_from_measures_in_tables()`
   - Lines 792-835: Improved method `_extract_table_references_from_measures()`
   - Changes: Column detection in ALL tables

## Included Tests

1. **[scripts/test_measure_dependencies.py](scripts/test_measure_dependencies.py)**
   - Verifies DAX dependency detection

2. **[scripts/test_empty_pages.py](scripts/test_empty_pages.py)**
   - Verifies `"pages"` is not in empty reports

3. **[scripts/test_debug_filtering.py](scripts/test_debug_filtering.py)**
   - Verifies detailed column filtering per table

4. **[scripts/check_measures.py](scripts/check_measures.py)**
   - Analyzes which columns each measure uses

5. **[test_relationships_filtering.py](test_relationships_filtering.py)**
   - Verifies selective relationship filtering

6. **[test_recursive_simple.py](test_recursive_simple.py)**
   - Verifies recursive table search

---

## Next Steps (Optional)

1. **Transitive DAX dependency analysis**: If Measure A uses Function B that references Table C
2. **Include report visual and filter references**: Analyze visuals in reports
3. **Model compression**: Remove unused hierarchies, optimize partitions
4. **Integrity validation**: Verify references in measures remain valid after filtering
