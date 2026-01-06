"""
Test simple para verificar que la búsqueda recursiva de tablas funciona
"""

from pathlib import Path
from models.semantic_model import SemanticModel

# Cargar el modelo FullAdventureWorks
full_model = SemanticModel(
    Path('Modelos/FullAdventureWorks.SemanticModel')
)
full_model.load_from_directory(full_model.base_path)

print("=" * 80)
print("TEST: Busqueda recursiva de tablas relacionadas")
print("=" * 80)

# Debug: revisar relaciones de FactInternetSales
print("\nRelaciones que incluyen FactInternetSales:")
for rel in full_model.relationships:
    if rel.from_table == "FactInternetSales" or rel.to_table == "FactInternetSales":
        cardinality = rel.cardinality or "manyToOne (implicito)"
        print(f"  {rel.from_table} -> {rel.to_table}: {cardinality}")

# Crear submodelo con FactInternetSales (recursive=True)
print("\nCreando submodelo con recursive=True, max_depth=2")
subset = full_model.create_subset_model(
    table_specs=["FactInternetSales"],
    subset_name="TestRecursive_Depth2",
    recursive=True,
    max_depth=2
)

print(f"\nTablas encontradas: {len(subset.tables)}")
for table in subset.tables:
    print(f"  - {table.name}")

print(f"\nRelaciones encontradas: {len(subset.relationships)}")
for i, rel in enumerate(subset.relationships[:15]):
    print(f"  {i+1}. {rel.from_table} -> {rel.to_table}")
if len(subset.relationships) > 15:
    print(f"  ... y {len(subset.relationships) - 15} mas")
