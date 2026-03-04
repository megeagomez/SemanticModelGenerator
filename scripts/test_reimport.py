"""
test_reimport.py
Reimporta tanto Reports como Modelos Semánticos desde carpetas locales a DuckDB,
sin conectar a Power BI (ConnectAndDownload=False).
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../Importer/src')))
from import_from_powerbi import PowerBIImporter, FabricItemDownloader


def main(db_path, reports_folder, workspace_name):
    db_name = os.path.splitext(os.path.basename(db_path))[0]

    downloader = FabricItemDownloader()
    importer = PowerBIImporter(downloader, workspace_name=workspace_name)

    print(f"=== Reimportación local ===")
    print(f"  BD destino : {db_path}")
    print(f"  Carpeta    : {reports_folder}")
    print(f"  Workspace  : {workspace_name}")
    print()

    importer.import_from_powerbi(
        destination_path=reports_folder,
        db_name=db_name,
        ConnectAndDownload=False
    )

    # Resumen: listar lo que se ha persistido
    try:
        import duckdb
        conn = duckdb.connect(db_path, read_only=True)

        models = conn.execute("SELECT name FROM semantic_model ORDER BY name").fetchall()
        reports = conn.execute("SELECT name FROM report ORDER BY name").fetchall()

        print()
        print(f"=== Resumen de la BD ({db_name}) ===")
        print(f"  Modelos semánticos: {len(models)}")
        for m in models:
            print(f"    - {m[0]}")
        print(f"  Reportes: {len(reports)}")
        for r in reports:
            print(f"    - {r[0]}")

        # Particiones si existen
        try:
            partitions = conn.execute("SELECT COUNT(*) FROM semantic_model_partitions").fetchone()
            print(f"  Particiones persistidas: {partitions[0]}")
        except Exception:
            pass

        conn.close()
    except Exception as e:
        print(f"  (No se pudo leer resumen de la BD: {e})")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Reimporta Reports y Modelos Semánticos locales a DuckDB (sin conexión a Power BI)."
    )
    parser.add_argument("--db", type=str, required=True, help="Ruta a la base DuckDB (ej: data/powerbi.duckdb)")
    parser.add_argument("--folder", type=str, required=True, help="Carpeta raíz con las carpetas .SemanticModel y .Report")
    parser.add_argument("--workspace", type=str, required=True, help="Nombre del workspace de Power BI")
    args = parser.parse_args()
    main(args.db, args.folder, args.workspace)
