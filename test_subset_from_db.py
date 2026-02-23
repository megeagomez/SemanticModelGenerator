"""Test create_subset_model_from_db con datos reales de testgc."""
from pathlib import Path
from models.semantic_model import SemanticModel

model_path = Path(r"D:\mcpdata\testgc\DemoAranzadi\TES - Gestión Comercial.SemanticModel")
db_path = r"D:\mcpdata\testgc\gc.duckdb"

print(f"Model path exists: {model_path.exists()}")
print(f"Model path: {model_path}")

model = SemanticModel(str(model_path))
model.load_from_directory(model_path)

print(f"\nLoaded: {model.base_path.name}")
print(f"  Tables: {len(model.tables)}")
print(f"  Relationships: {len(model.relationships)}")
print(f"  semantic_model_id: {model.semantic_model_id}")

if model.tables:
    print("\nTable names (first 10):")
    for t in sorted(model.tables, key=lambda x: x.name)[:10]:
        print(f"  {t.name}: {len(t.columns)} cols, {len(t.measures)} measures")

# Config se guarda en la misma carpeta del modelo
config_path = model_path.parent / "TestFromDB.SemanticModel_config.json"

subset = model.create_subset_model_from_db(
    db_path=db_path,
    subset_name="TestFromDB.SemanticModel",
    config_path=config_path,
)

print(f"\n=== RESULTADO ===")
print(f"  Subset tables: {len(subset.tables)}")
print(f"  Subset relationships: {len(subset.relationships)}")
for t in sorted(subset.tables, key=lambda x: x.name):
    print(f"  {t.name}: {len(t.columns)} cols, {len(t.measures)} measures")
