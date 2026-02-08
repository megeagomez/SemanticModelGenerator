import pickle
import sys
import os
import duckdb
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from models.semantic_model import SemanticModel
from models.report import clsReport
from FabricItemDownloader import FabricItemDownloader
import json





class PowerBIImporter:
    def __init__(self, fabric_item_downloader: FabricItemDownloader, workspace_name: str = None):
        self.fabric_item_downloader = fabric_item_downloader
        self.workspace_name = workspace_name

    def import_from_powerbi(self, item_id: str = None, destination_path: str = "data", WorkspaceName: str = None, db_name: str = "powerbi"):
        """
        Importa todos los modelos semánticos y reports de un workspace de Power BI, identificado por nombre.
        Si WorkspaceName es None, se usará el primer workspace disponible.
        
        Args:
            item_id: ID del item específico (no usado actualmente)
            destination_path: Ruta base para descargar archivos (default: "data")
            WorkspaceName: Nombre del workspace a importar
            db_name: Nombre de la base de datos DuckDB en carpeta data (default: "powerbi")
        """
        # 0. Login si es necesario
        if not self.fabric_item_downloader.access_token:
            if not self.fabric_item_downloader.authenticate():
                raise Exception("No se pudo autenticar con Power BI.")

        # 1. Listar workspaces
        workspaces = self.fabric_item_downloader.list_workspaces()
        if not workspaces:
            raise Exception("No se encontraron workspaces disponibles.")

        # 2. Buscar workspace por nombre
        ws = None
        # Prioridad: parámetro WorkspaceName > self.workspace_name > primero disponible
        ws_name = WorkspaceName or self.workspace_name
        if ws_name:
            for w in workspaces:
                if w.get('displayName', '').lower() == ws_name.lower():
                    ws = w
                    break
            if not ws:
                raise Exception(f"No se encontró el workspace con nombre: {ws_name}")
        else:
            ws = workspaces[0]

        workspace_id = ws['id']
        workspace_name = ws.get('displayName', workspace_id)


        # Archivo de información global
        info_path = os.path.join(destination_path, "powerbiinfo.json")
        if os.path.exists(info_path):
            with open(info_path, "r", encoding="utf-8") as f:
                powerbiinfo = json.load(f)
        else:
            powerbiinfo = {"workspaces": []}

        # Buscar o crear entrada de workspace
        ws_entry = next((w for w in powerbiinfo["workspaces"] if w["id"] == workspace_id), None)
        if not ws_entry:
            ws_entry = {"id": workspace_id, "name": workspace_name, "reports": [], "semantic_models": []}
            powerbiinfo["workspaces"].append(ws_entry)
        else:
            ws_entry["name"] = workspace_name  # Actualiza nombre si cambió


        # Descargar modelos semánticos y parsear/serializar
        semantic_models = self.fabric_item_downloader.list_semantic_models(workspace_id)
        ws_entry["semantic_models"] = []
        output_dir = os.path.join("output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Crear conexión DuckDB
        db_path = os.path.join(destination_path, f"{db_name}.duckdb")
        conn = duckdb.connect(db_path)
        for model in semantic_models:
            model_id = model.get("id")
            model_name = model.get("displayName", model_id)
            ws_entry["semantic_models"].append({"id": model_id, "name": model_name})
            self.fabric_item_downloader.download_semantic_model(workspace_id, model_id, output_folder=destination_path)
            # Parsear y serializar
            model_base_path = os.path.join(destination_path, workspace_name, model_name)
            if os.path.exists(model_base_path):
                try:
                    semantic_model_obj = SemanticModel(model_base_path, semantic_model_id=model_id, workspace_id=workspace_id)
                    semantic_model_obj.load_from_directory(Path(model_base_path))
                    semantic_model_obj.save_to_database(conn)
                    with open(os.path.join(output_dir, f"{workspace_name}__{model_name}__semantic_model.pkl"), "wb") as pf:
                        pickle.dump(semantic_model_obj, pf)
                except Exception as e:
                    print(f"Error parseando/serializando modelo {model_name}: {e}")
                

        # Descargar reports y parsear/serializar
        reports = self.fabric_item_downloader.list_reports(workspace_id)
        ws_entry["reports"] = []
        for report in reports:
            report_id = report.get("id")
            report_name = report.get("displayName", report_id)
            ws_entry["reports"].append({"id": report_id, "name": report_name})
            self.fabric_item_downloader.download(workspace_id, report_id, output_folder=destination_path)
            # Parsear y serializar
            report_folder = os.path.join(destination_path, workspace_name, report_name)
            try:
                report_obj = clsReport(report_folder, report_id=report_id, workspace_id=workspace_id)
                report_obj.save_to_database(conn)
                with open(os.path.join(output_dir, f"{workspace_name}__{report_name}__report.pkl"), "wb") as pf:
                    pickle.dump(report_obj, pf)
            except Exception as e:
                print(f"Error parseando/serializando report {report_name}: {e}")

        # Guardar info actualizada
        os.makedirs(destination_path, exist_ok=True)
        with open(info_path, "w", encoding="utf-8") as f:
            json.dump(powerbiinfo, f, indent=2, ensure_ascii=False)

        # Cerrar conexión DuckDB
        conn.close()
        print(f"✅ Base de datos DuckDB guardada en: {db_path}")




if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Importa modelos y reports de Power BI de un workspace específico.")
    parser.add_argument("--workspace", type=str, help="Nombre del workspace a importar", required=False)
    parser.add_argument("--dest", type=str, help="Directorio destino para la descarga", default="data")
    parser.add_argument("--db", type=str, help="Nombre de la base de datos DuckDB (sin extensión)", default="powerbi")
    args = parser.parse_args()

    downloader = FabricItemDownloader()
    importer = PowerBIImporter(downloader, workspace_name=args.workspace)
    importer.import_from_powerbi(destination_path=args.dest, db_name=args.db)

