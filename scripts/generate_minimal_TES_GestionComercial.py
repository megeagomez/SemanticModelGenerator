import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.semantic_model import SemanticModel

if __name__ == "__main__":
    db_path = r"D:\Modelos\toyotamodels.duckdb"
    semantic_model_dir = r"D:\Modelos\TES - CONCESIONARIOS\TES - Gestión Comercial.SemanticModel"
    subset_name = "TES_GestionComercial_minimomeg.SemanticModel"

    # Cargar el modelo base desde disco
    model = SemanticModel(semantic_model_dir)
    model.load_from_directory(model.base_path)

    # Generar el submodelo mínimo
    subset_model = model.create_subset_model_from_db(
        db_path=db_path,
        subset_name=subset_name,
        semantic_model_id=129,
        config_path=None,
        create_pbip=True
    )

    # Guardar la carpeta .SemanticModel en disco
    subset_model.save_to_directory(subset_model.base_path)

    print(f"Submodelo generado y guardado en: {subset_model.base_path}")
