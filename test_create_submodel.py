"""Test create_subset_model_from_db con demo.duckdb (DemoADN workspace)."""
import sys
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
from models.semantic_model import SemanticModel

# ── Configuración ────────────────────────────────────────────
DB_PATH = r"D:\mcpdata\demotest\demo.duckdb"
WORKSPACE_DIR = Path(r"D:\mcpdata\demotest\DemoADN")
SOURCE_MODEL = "semanticAdventureworks.SemanticModel"
TARGET_MODEL = "SubmodelADN.SemanticModel"

source_path = WORKSPACE_DIR / SOURCE_MODEL
target_path = WORKSPACE_DIR / TARGET_MODEL
config_path = WORKSPACE_DIR / f"{TARGET_MODEL}_config.json"

# ── Validaciones ─────────────────────────────────────────────
print(f"DB path exists:    {Path(DB_PATH).exists()}")
print(f"Source model:      {source_path}")
print(f"Source exists:     {source_path.exists()}")
print(f"Target model:      {target_path}")

# ── Cargar modelo fuente ─────────────────────────────────────
model = SemanticModel(str(source_path))
model.load_from_directory(source_path)

print(f"\n{'='*60}")
print(f"Modelo fuente: {model.base_path.name}")
print(f"{'='*60}")
print(f"  Tablas:        {len(model.tables)}")
print(f"  Relaciones:    {len(model.relationships)}")

if model.tables:
    print("\nTablas originales:")
    for t in sorted(model.tables, key=lambda x: x.name):
        print(f"  {t.name}: {len(t.columns)} cols, {len(t.measures)} measures")

# ── Crear submodelo desde DuckDB ─────────────────────────────
print(f"\n{'='*60}")
print(f"Creando submodelo: {TARGET_MODEL}")
print(f"{'='*60}")

subset = model.create_subset_model_from_db(
    db_path=DB_PATH,
    subset_name=TARGET_MODEL,
    config_path=config_path,
)

# ── Resultado ────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"RESULTADO")
print(f"{'='*60}")
print(f"  Tablas subset:       {len(subset.tables)}")
print(f"  Relaciones subset:   {len(subset.relationships)}")

if subset.tables:
    print("\nTablas en submodelo:")
    for t in sorted(subset.tables, key=lambda x: x.name):
        orig = next((ot for ot in model.tables if ot.name == t.name), None)
        orig_cols = len(orig.columns) if orig else "?"
        has_rc = any("RemoveColumns" in (p.source_expression or "") for p in t.partitions)
        rc_flag = " [RemoveColumns]" if has_rc else ""
        print(f"  {t.name}: {orig_cols} -> {len(t.columns)} cols, "
              f"{len(t.measures)} measures{rc_flag}")

# ── Guardar submodelo ────────────────────────────────────────
print(f"\nGuardando submodelo en: {target_path}")
subset.save_to_directory(target_path)
print(f"✅ Submodelo guardado correctamente")

# ── Verificar que se puede recargar ──────────────────────────
print(f"\nVerificando recarga del submodelo...")
reloaded = SemanticModel(str(target_path))
reloaded.load_from_directory(target_path)
print(f"  Tablas recargadas:     {len(reloaded.tables)}")
print(f"  Relaciones recargadas: {len(reloaded.relationships)}")
print(f"✅ Recarga OK")
