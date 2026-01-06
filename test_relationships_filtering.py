"""
Test para verificar que las relaciones se filtran correctamente
en los modelos mínimos (subset models).

El objetivo es que SOLO se incluyan relaciones entre tablas
que se usan realmente (directamente en initial_tables o indirectamente
a través de referencias en medidas DAX).
"""

from pathlib import Path
from models.semantic_model import SemanticModel

# Cargar el modelo FullAdventureWorks
full_model = SemanticModel(
    Path('Modelos/FullAdventureWorks.SemanticModel')
)
full_model.load_from_directory(full_model.base_path)

print("=" * 80)
print("MODELO ORIGINAL")
print("=" * 80)
print(f"Total de tablas: {len(full_model.tables)}")
print(f"Total de relaciones: {len(full_model.relationships)}")
print("\nRelaciones del modelo completo:")
for i, rel in enumerate(full_model.relationships[:10]):  # Primeras 10
    cardinality = rel.cardinality or "manyToOne (implícito)"
    active = "activa" if rel.is_active else "inactiva"
    print(f"  {i+1}. {rel.from_table} -> {rel.to_table}: {cardinality}, {active}")
if len(full_model.relationships) > 10:
    print(f"  ... y {len(full_model.relationships) - 10} más")

# Crear submodelo SOLO con FactInternetSales (recursive=False)
print("\n" + "=" * 80)
print("SUBMODELO: Solo FactInternetSales (recursive=False)")
print("=" * 80)

subset1 = full_model.create_subset_model(
    table_specs=["FactInternetSales"],
    subset_name="TestMinimal_FactOnly",
    recursive=False
)

print(f"\nTablas en el submodelo: {len(subset1.tables)}")
for table in subset1.tables:
    print(f"  - {table.name}")

print(f"\nRelaciones en el submodelo: {len(subset1.relationships)}")
for i, rel in enumerate(subset1.relationships):
    cardinality = rel.cardinality or "manyToOne (implícito)"
    active = "activa" if rel.is_active else "inactiva"
    print(f"  {i+1}. {rel.from_table} -> {rel.to_table}: {cardinality}, {active}")

if len(subset1.relationships) > 0:
    print("\nADVERTENCIA: No deberia haber relaciones cuando solo hay una tabla!")
else:
    print("\nCORRECTO: No hay relaciones para una tabla individual")

# Crear submodelo con FactInternetSales + DimProduct (recursive=False)
print("\n" + "=" * 80)
print("SUBMODELO: FactInternetSales + DimProduct (recursive=False)")
print("=" * 80)

subset2 = full_model.create_subset_model(
    table_specs=["FactInternetSales", "DimProduct"],
    subset_name="TestMinimal_FactProduct",
    recursive=False
)

print(f"\nTablas en el submodelo: {len(subset2.tables)}")
for table in subset2.tables:
    print(f"  - {table.name}")

print(f"\nRelaciones en el submodelo: {len(subset2.relationships)}")
for i, rel in enumerate(subset2.relationships):
    cardinality = rel.cardinality or "manyToOne (implícito)"
    active = "activa" if rel.is_active else "inactiva"
    print(f"  {i+1}. {rel.from_table} -> {rel.to_table}: {cardinality}, {active}")

# Verificar que solo hay relaciones entre FactInternetSales y DimProduct
expected_relations = 1  # FactInternetSales -> DimProduct
if len(subset2.relationships) == expected_relations:
    print(f"\nCORRECTO: {expected_relations} relacion (FactInternetSales <-> DimProduct)")
else:
    print(f"\nERROR: Se esperaban {expected_relations} relaciones, pero hay {len(subset2.relationships)}")

# Crear submodelo con FactInternetSales (recursive=True para explorar todas las relaciones)
print("\n" + "=" * 80)
print("SUBMODELO: FactInternetSales (recursive=True)")
print("=" * 80)

subset3 = full_model.create_subset_model(
    table_specs=["FactInternetSales"],
    subset_name="TestMinimal_FactRecursive",
    recursive=True,
    max_depth=3
)

print(f"\nTablas en el submodelo: {len(subset3.tables)}")
for table in subset3.tables:
    print(f"  - {table.name}")

print(f"\nRelaciones en el submodelo: {len(subset3.relationships)}")
for i, rel in enumerate(subset3.relationships[:10]):
    cardinality = rel.cardinality or "manyToOne (implícito)"
    active = "activa" if rel.is_active else "inactiva"
    print(f"  {i+1}. {rel.from_table} -> {rel.to_table}: {cardinality}, {active}")
if len(subset3.relationships) > 10:
    print(f"  ... y {len(subset3.relationships) - 10} más")

# Verificar que TODAS las relaciones incluidas tienen ambas tablas en el submodelo
subset3_table_names = {t.name for t in subset3.tables}
invalid_relations = []
for rel in subset3.relationships:
    if rel.from_table not in subset3_table_names or rel.to_table not in subset3_table_names:
        invalid_relations.append(rel)

if not invalid_relations:
    print(f"\nCORRECTO: Todas las relaciones tienen ambas tablas en el submodelo")
else:
    print(f"\nERROR: {len(invalid_relations)} relaciones con tablas faltantes:")
    for rel in invalid_relations[:5]:
        print(f"  - {rel.from_table} -> {rel.to_table}")

# Resumen
print("\n" + "=" * 80)
print("RESUMEN")
print("=" * 80)
print(f"Modelo original:")
print(f"  - Tablas: {len(full_model.tables)}")
print(f"  - Relaciones: {len(full_model.relationships)}")
print(f"\nSubmodelo 1 (FactInternetSales solo, recursive=False):")
print(f"  - Tablas: {len(subset1.tables)}")
print(f"  - Relaciones: {len(subset1.relationships)}")
print(f"\nSubmodelo 2 (FactInternetSales + DimProduct, recursive=False):")
print(f"  - Tablas: {len(subset2.tables)}")
print(f"  - Relaciones: {len(subset2.relationships)}")
print(f"\nSubmodelo 3 (FactInternetSales, recursive=True, max_depth=3):")
print(f"  - Tablas: {len(subset3.tables)}")
print(f"  - Relaciones: {len(subset3.relationships)}")
