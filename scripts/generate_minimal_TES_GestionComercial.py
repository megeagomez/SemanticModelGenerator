import sys
import os
import argparse
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.semantic_model import SemanticModel

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate minimal subset model")
    parser.add_argument("--db-path", default=r"D:\Modelos\toyotamodels.duckdb", 
                        help="Path to DuckDB database")
    parser.add_argument("--semantic-model-dir", default=r"D:\Modelos\TES - CONCESIONARIOS\TES - Gestión Comercial.SemanticModel",
                        help="Path to semantic model directory")
    parser.add_argument("--subset-name", default="TES_GestionComercial_minimomeg.SemanticModel",
                        help="Name for the subset model")
    args = parser.parse_args()
    
    db_path = args.db_path
    semantic_model_dir = args.semantic_model_dir
    subset_name = args.subset_name

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
