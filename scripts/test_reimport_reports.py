import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../Importer/src')))
from import_from_powerbi import PowerBIImporter, FabricItemDownloader

def main(db_path, reports_folder, workspace_name):
    # Extraer nombre de la base sin extensión y carpeta destino de la ruta de la BD
    db_name = os.path.splitext(os.path.basename(db_path))[0]
    db_dir = os.path.dirname(db_path) or reports_folder
    # Instanciar downloader y importer
    downloader = FabricItemDownloader()
    importer = PowerBIImporter(downloader, workspace_name=workspace_name)
    # Ejecutar solo parseo y persistencia local (sin conectar a Power BI)
    importer.import_from_powerbi(destination_path=reports_folder, db_name=db_name, ConnectAndDownload=False)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test reimport Power BI reports to DuckDB.")
    parser.add_argument("--db", type=str, required=True, help="Ruta a la base DuckDB (ej: data/powerbi.duckdb)")
    parser.add_argument("--folder", type=str, required=True, help="Carpeta destino para reports/modelos")
    parser.add_argument("--workspace", type=str, required=True, help="Nombre del workspace de Power BI")
    args = parser.parse_args()
    main(args.db, args.folder, args.workspace)
