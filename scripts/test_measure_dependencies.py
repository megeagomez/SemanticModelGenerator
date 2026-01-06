"""
Script de prueba para verificar detección de dependencias de tablas y columnas en medidas DAX
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.semantic_model import SemanticModel

# Cargar modelo FullAdventureWorks
model_path = Path(r"d:\Python apps\pyconstelaciones + Reports\Modelos\FullAdventureWorks.SemanticModel")
model = SemanticModel(str(model_path))
model.load_from_directory(model_path)

print(f"Modelo cargado: {model.model.name if model.model else 'Sin nombre'}")
print(f"Total tablas: {len(model.tables)}")
print(f"Total relaciones: {len(model.relationships)}")

# Buscar la medida "mi media" en FactInternetSales
fact_table = next((t for t in model.tables if t.name == "FactInternetSales"), None)
if fact_table:
    mi_media = next((m for m in fact_table.measures if m.name == "mi media"), None)
    if mi_media:
        print(f"\nMedida encontrada: {mi_media.name}")
        print(f"Expresión: {mi_media.expression}")
    else:
        print("\nMedida 'mi media' no encontrada")
else:
    print("\nTabla FactInternetSales no encontrada")

# Crear subset con solo FactInternetSales (sin recursive)
print("\n" + "="*60)
print("Creando subset con FactInternetSales (recursive=False)")
print("="*60)

subset = model.create_subset_model(
    table_specs=[("FactInternetSales", "ManyToOne")],
    subset_name="TestDependencies",
    recursive=False
)

print(f"\nTablas en subset:")
for table in sorted([t.name for t in subset.tables]):
    print(f"  - {table}")

# Verificar si DimProduct está incluida y revisar sus columnas
print("\n" + "="*60)
print("Verificación de DimProduct")
print("="*60)

if any(t.name == "DimProduct" for t in subset.tables):
    dimproduct_subset = next(t for t in subset.tables if t.name == "DimProduct")
    print(f"\n✓ DimProduct fue incluida automáticamente")
    print(f"  Columnas en subset: {[col.name for col in dimproduct_subset.columns]}")
    
    # Verificar si tiene solo ProductKey (+ posibles columnas de relación)
    column_names = {col.name for col in dimproduct_subset.columns}
    if "ProductKey" in column_names:
        print(f"  ✓ ProductKey incluida (usada en medida 'mi media')")
    else:
        print(f"  ✗ ProductKey NO está incluida (debería estar)")
    
    # Comparar con tabla original
    dimproduct_original = next(t for t in model.tables if t.name == "DimProduct")
    original_cols = len(dimproduct_original.columns)
    subset_cols = len(dimproduct_subset.columns)
    print(f"\n  Comparación:")
    print(f"  - Columnas en modelo original: {original_cols}")
    print(f"  - Columnas en subset: {subset_cols}")
    print(f"  - Reducción: {original_cols - subset_cols} columnas eliminadas")
else:
    print("\n✗ DimProduct NO fue incluida (debería haberse agregado)")
