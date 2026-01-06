"""
Script de prueba detallado para verificar filtrado de columnas
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.semantic_model import SemanticModel

# Cargar modelo FullAdventureWorks
model_path = Path(r"d:\Python apps\pyconstelaciones + Reports\Modelos\FullAdventureWorks.SemanticModel")
model = SemanticModel(str(model_path))
model.load_from_directory(model_path)

print("="*70)
print("VERIFICACIÓN DE FILTRADO DE COLUMNAS")
print("="*70)

# Información original
fact_table = next(t for t in model.tables if t.name == "FactInternetSales")
dimproduct_orig = next(t for t in model.tables if t.name == "DimProduct")

print(f"\nModelo original:")
print(f"  FactInternetSales: {len(fact_table.columns)} columnas, {len(fact_table.measures)} medidas")
print(f"  DimProduct: {len(dimproduct_orig.columns)} columnas")

# Buscar medida "mi media"
mi_media = next((m for m in fact_table.measures if m.name == "mi media"), None)
if mi_media:
    print(f"\nMedida 'mi media' encontrada:")
    print(f"  Expresión: {mi_media.expression}")

# Crear subset
print("\n" + "="*70)
print("CREANDO SUBSET")
print("="*70)

subset = model.create_subset_model(
    table_specs=[("FactInternetSales", "ManyToOne")],
    subset_name="TestDebug",
    recursive=False
)

print("\n" + "="*70)
print("RESULTADO DEL SUBSET")
print("="*70)

# Verificar qué hay en el subset
fact_subset = next((t for t in subset.tables if t.name == "FactInternetSales"), None)
dimproduct_subset = next((t for t in subset.tables if t.name == "DimProduct"), None)

if fact_subset:
    print(f"\nFactInternetSales en subset:")
    print(f"  Columnas: {len(fact_subset.columns)}")
    print(f"  Medidas: {len(fact_subset.measures)}")
    if len(fact_subset.columns) < 50:
        print(f"  Nombres de columnas: {[c.name for c in fact_subset.columns]}")

if dimproduct_subset:
    print(f"\nDimProduct en subset:")
    print(f"  Columnas: {len(dimproduct_subset.columns)}")
    print(f"  Nombres de columnas: {[c.name for c in dimproduct_subset.columns]}")
    
    # Comparación
    reduction = len(dimproduct_orig.columns) - len(dimproduct_subset.columns)
    print(f"\n  Reducción: {len(dimproduct_orig.columns)} → {len(dimproduct_subset.columns)} ({reduction} menos)")
    
    # Verificar si contiene ProductKey
    has_productkey = any(c.name == "ProductKey" for c in dimproduct_subset.columns)
    print(f"  Tiene ProductKey: {has_productkey}")
    
    # Verificar columns en el raw_content
    print(f"\n  Raw content (primeras 500 caracteres):")
    print(f"  {dimproduct_subset.raw_content[:500]}")
else:
    print("\nDimProduct NO está en el subset!")

# Verificar table_elements en config
config_path = model.base_path.parent / "TestDebug_config.json"
if config_path.exists():
    import json
    with open(config_path) as f:
        config = json.load(f)
    
    print(f"\n" + "="*70)
    print("CONFIGURACIÓN GUARDADA")
    print("="*70)
    
    if "table_elements" in config and config["table_elements"]:
        print(f"\nTable elements en config:")
        for table_name, spec in config["table_elements"].items():
            print(f"  {table_name}:")
            print(f"    columns: {spec.get('columns')}")
            print(f"    mode: {spec.get('mode')}")
    else:
        print(f"\nNo hay table_elements en config")
