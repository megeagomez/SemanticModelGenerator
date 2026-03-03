import pickle
import sys
import os
import duckdb
from pathlib import Path
import json
import logging
import threading
from typing import Any

# Añadir el directorio actual y el raíz al path
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.abspath(os.path.join(current_dir, '../../')))

from models.semantic_model import SemanticModel
from models.report import clsReport
from models.workspace import Workspace
from models.dax_tokenizer import DaxTokenizer
from FabricItemDownloader import FabricItemDownloader

logger = logging.getLogger(__name__)

# Variable global para mantener el downloader y el flow activo
_active_auth_flow: dict[str, Any] = {"downloader": None, "flow": None, "message": None, "thread": None}

# Ruta global configurable para datos
_data_path = Path("D:/mcpdata")


def set_data_path(path: str) -> None:
    """Configura la ruta global para datos, caché y BD.
    
    Args:
        path: Ruta absoluta o relativa donde guardar datos (ej: "D:/mcpdata")
    """
    global _data_path
    _data_path = Path(path)
    _data_path.mkdir(parents=True, exist_ok=True)


def start_device_flow_interactive():
    """Inicia el device flow y devuelve el mensaje (link + código) SIN bloquear."""
    from msal import PublicClientApplication
    from datetime import datetime
    
    try:
        downloader = FabricItemDownloader()
        
        # Si ya hay un token válido, informar
        cached_token = downloader.load_token_from_file()
        if cached_token:
            downloader.access_token = cached_token
            _active_auth_flow["downloader"] = downloader
            msg = "✅ Ya hay un token válido guardado. No es necesario hacer login."
            print(msg, flush=True)
            logger.info(msg)
            return {"success": True, "message": msg, "already_authenticated": True}
        
        # Iniciar device flow
        app = PublicClientApplication(
            downloader.config["client_id"],
            authority=downloader.config["authority"]
        )
        
        flow = app.initiate_device_flow(scopes=downloader.config["scopes"])
        if "user_code" not in flow:
            error_msg = f"Error iniciando device flow: {flow.get('error_description')}"
            print(f"❌ {error_msg}", flush=True)
            return {"success": False, "message": error_msg}
        
        message = flow["message"]
        
        # IMPRIMIR EL MENSAJE POR CONSOLA para que sea visible
        print("\n" + "="*60, flush=True)
        print("🔐 POWER BI - AUTENTICACIÓN INTERACTIVA", flush=True)
        print("="*60, flush=True)
        print(message, flush=True)
        print("="*60 + "\n", flush=True)
        
        # Guardar el flow y downloader para completar después
        _active_auth_flow["downloader"] = downloader
        _active_auth_flow["flow"] = flow
        _active_auth_flow["message"] = message
        _active_auth_flow["app"] = app
        _active_auth_flow["status"] = "waiting"
        
        # Iniciar thread para completar la autenticación en segundo plano
        def complete_auth():
            try:
                print("⏳ Esperando que completes la autenticación en el navegador...", flush=True)
                result = app.acquire_token_by_device_flow(flow)
                if "access_token" in result:
                    downloader.access_token = result["access_token"]
                    downloader.save_token_to_file(downloader.access_token)
                    
                    # Guardar archivo de estado
                    status_file = _data_path / "powerbi_auth_status.json"
                    status_file.parent.mkdir(exist_ok=True)
                    status_data = {
                        "authenticated": True,
                        "timestamp": datetime.now().isoformat(),
                        "message": "Autenticación completada exitosamente"
                    }
                    status_file.write_text(json.dumps(status_data, indent=2))
                    
                    _active_auth_flow["status"] = "completed"
                    success_msg = "✅ Autenticación completada exitosamente en segundo plano"
                    print("\n" + "="*60, flush=True)
                    print(success_msg, flush=True)
                    print("="*60 + "\n", flush=True)
                    logger.info(success_msg)
                else:
                    error_msg = f"❌ Error en autenticación: {result.get('error_description')}"
                    _active_auth_flow["status"] = "failed"
                    print(error_msg, flush=True)
                    logger.error(error_msg)
            except Exception as e:
                error_msg = f"❌ Error completando autenticación: {e}"
                _active_auth_flow["status"] = "failed"
                print(error_msg, flush=True)
                logger.error(error_msg)
        
        thread = threading.Thread(target=complete_auth, daemon=True)
        thread.start()
        _active_auth_flow["thread"] = thread
        
        return {"success": True, "message": message, "already_authenticated": False}
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"❌ {error_msg}", flush=True)
        return {"success": False, "message": error_msg}


def check_auth_status():
    """Verifica si la autenticación se completó."""
    # Primero verificar si hay archivo de estado
    status_file = _data_path / "powerbi_auth_status.json"
    if status_file.exists():
        try:
            status_data = json.loads(status_file.read_text())
            if status_data.get("authenticated"):
                return {"authenticated": True, "message": f"✅ {status_data.get('message', 'Autenticado')} (desde {status_data.get('timestamp', 'N/A')})"}
        except Exception:
            pass
    
    if not _active_auth_flow.get("downloader"):
        # Verificar si hay token en cache
        try:
            downloader = FabricItemDownloader()
            cached_token = downloader.load_token_from_file()
            if cached_token:
                return {"authenticated": True, "message": "✅ Hay un token válido en caché"}
        except Exception:
            pass
        return {"authenticated": False, "message": "⚠️ No hay proceso de autenticación activo. Ejecuta powerbi_login_interactive primero."}
    
    downloader = _active_auth_flow["downloader"]
    status = _active_auth_flow.get("status", "unknown")
    
    if status == "completed" and downloader.access_token:
        return {"authenticated": True, "message": "✅ Autenticación completada exitosamente"}
    
    if status == "failed":
        return {"authenticated": False, "message": "❌ La autenticación falló. Intenta ejecutar powerbi_login_interactive nuevamente."}
    
    # Verificar si el thread sigue corriendo
    thread = _active_auth_flow.get("thread")
    if thread and thread.is_alive():
        return {"authenticated": False, "message": "⏳ Esperando que completes el login en el navegador... (revisa la consola del servidor)"}
    else:
        # Thread terminó pero no hay token
        if downloader.access_token:
            return {"authenticated": True, "message": "✅ Autenticación completada"}
        else:
            return {"authenticated": False, "message": "❌ El login no se completó o expiró. Intenta nuevamente."}


def get_authenticated_downloader():
    """Obtiene una instancia de FabricItemDownloader autenticada."""
    # Intentar reutilizar el downloader del auth flow
    if _active_auth_flow.get("downloader") and _active_auth_flow["downloader"].access_token:
        return _active_auth_flow["downloader"]
    
    # Si no, crear uno nuevo e intentar cargar el token del cache
    downloader = FabricItemDownloader()
    cached_token = downloader.load_token_from_file()
    if cached_token:
        downloader.access_token = cached_token
        return downloader
    
    # No hay token disponible
    return None


def powerbi_list_workspaces():
    """Lista todos los workspaces disponibles."""
    downloader = get_authenticated_downloader()
    if not downloader:
        return {"success": False, "message": "⚠️ No estás autenticado. Ejecuta powerbi_login_interactive primero."}
    
    try:
        workspaces = downloader.list_workspaces()
        return {"success": True, "workspaces": workspaces}
    except Exception as e:
        return {"success": False, "message": f"❌ Error listando workspaces: {str(e)}"}


def powerbi_list_reports(workspace_id: str):
    """Lista todos los reportes de un workspace."""
    downloader = get_authenticated_downloader()
    if not downloader:
        return {"success": False, "message": "⚠️ No estás autenticado. Ejecuta powerbi_login_interactive primero."}
    
    try:
        reports = downloader.list_reports(workspace_id)
        return {"success": True, "reports": reports}
    except Exception as e:
        return {"success": False, "message": f"❌ Error listando reportes: {str(e)}"}


def powerbi_list_semantic_models(workspace_id: str):
    """Lista todos los modelos semánticos de un workspace."""
    downloader = get_authenticated_downloader()
    if not downloader:
        return {"success": False, "message": "⚠️ No estás autenticado. Ejecuta powerbi_login_interactive primero."}
    
    try:
        models = downloader.list_semantic_models(workspace_id)
        return {"success": True, "models": models}
    except Exception as e:
        return {"success": False, "message": f"❌ Error listando modelos semánticos: {str(e)}"}


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

        # Crear conexión DuckDB (PASO PREVIO antes de procesar modelos y reportes)
        db_path = os.path.join(destination_path, f"{db_name}.duckdb")
        os.makedirs(destination_path, exist_ok=True)
        conn = duckdb.connect(db_path)
        logger.info(f"📊 Base de datos DuckDB creada en: {db_path}")
        
        # GUARDAR WORKSPACES EN LA BD (paso previo orquestado)
        logger.info(f"💾 Guardando información de workspaces en BD...")
        for ws_data in workspaces:
            try:
                workspace_obj = Workspace.from_powerbi_response(ws_data)
                workspace_obj.save_to_database(conn)
                logger.info(f"✅ Workspace guardado: {workspace_obj.displayName}")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo guardar workspace {ws_data.get('displayName')}: {e}")
        
        logger.info(f"✅ Workspaces guardados en BD")
        
        # Descargar modelos semánticos y parsear/serializar
        semantic_models = self.fabric_item_downloader.list_semantic_models(workspace_id)
        ws_entry["semantic_models"] = []
        output_dir = os.path.join("output")
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"📥 Procesando {len(semantic_models)} modelos semánticos...")
        for model in semantic_models:
            model_id = model.get("id")
            model_name = model.get("displayName", model_id)
            logger.info(f"📥 Descargando modelo: {model_name}...")
            ws_entry["semantic_models"].append({"id": model_id, "name": model_name})
            self.fabric_item_downloader.download_semantic_model(workspace_id, model_id, output_folder=destination_path)
            # Parsear y serializar
            # Los archivos se descargan en formato: {destination_path}/{workspace_name}/{proyecto}.SemanticModel/
            safe_workspace_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in workspace_name.strip())
            safe_model_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in model_name.strip())
            model_base_path = os.path.join(destination_path, safe_workspace_name, f"{safe_model_name}.SemanticModel")
            logger.info(f"🔍 Buscando archivos del modelo en: {model_base_path}")
            if os.path.exists(model_base_path):
                try:
                    logger.info(f"✅ Parseando modelo {model_name}...")
                    semantic_model_obj = SemanticModel(model_base_path, semantic_model_id=model_id, workspace_id=workspace_id)
                    semantic_model_obj.load_from_directory(Path(model_base_path))
                    semantic_model_obj.save_to_database(conn)
                    #get_calc_dependencies_paginated(self.fabric_item_downloader, model_id, model_name)
                    with open(os.path.join(output_dir, f"{workspace_name}__{model_name}__semantic_model.pkl"), "wb") as pf:
                        pickle.dump(semantic_model_obj, pf)
                    logger.info(f"✅ Modelo {model_name} procesado correctamente")
                except Exception as e:
                    logger.error(f"❌ Error parseando/serializando modelo {model_name}: {e}")
                    print(f"Error parseando/serializando modelo {model_name}: {e}")
            else:
                logger.error(f"❌ Carpeta del modelo no encontrada: {model_base_path}")
                print(f"⚠️ Carpeta del modelo no encontrada: {model_base_path}")
        
        # Consultar y guardar CALC_DEPENDENCIES (solo si workspace es Premium/PPU)
        # NOTA: DISCOVER_CALC_DEPENDENCIES es un DMV y actualmente no está disponible
        # a través del REST API ExecuteQueries (solo acepta DAX queries)
        # Esta funcionalidad queda pendiente para integración futura via XMLA endpoint
        
        print(f"⏭️  DISCOVER_CALC_DEPENDENCIES no disponible en workspace estándar (requiere Premium/PPU con XMLA)")

        # Descargar reports y parsear/serializar
        reports = self.fabric_item_downloader.list_reports(workspace_id)
        ws_entry["reports"] = []
        logger.info(f"📥 Procesando {len(reports)} reportes...")
        for report in reports:
            report_id = report.get("id")
            report_name = report.get("displayName", report_id)
            logger.info(f"📥 Descargando reporte: {report_name}...")
            ws_entry["reports"].append({"id": report_id, "name": report_name})
            self.fabric_item_downloader.download(workspace_id, report_id, output_folder=destination_path)
            # Parsear y serializar
            # Los archivos se descargan en formato: {destination_path}/{workspace_name}/{proyecto}.Report/
            safe_workspace_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in workspace_name.strip())
            safe_report_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in report_name.strip())
            report_folder = os.path.join(destination_path, safe_workspace_name, f"{safe_report_name}.Report")
            logger.info(f"🔍 Buscando archivos del reporte en: {report_folder}")
            if os.path.exists(report_folder):
                try:
                    logger.info(f"✅ Parseando reporte {report_name}...")
                    report_obj = clsReport(report_folder, report_id=report_id, workspace_id=workspace_id, report_name=report_name)
                    report_obj.save_to_database(conn)
                    with open(os.path.join(output_dir, f"{workspace_name}__{report_name}__report.pkl"), "wb") as pf:
                        pickle.dump(report_obj, pf)
                    logger.info(f"✅ Reporte {report_name} procesado correctamente")
                except Exception as e:
                    logger.error(f"❌ Error parseando/serializando report {report_name}: {e}")
                    print(f"Error parseando/serializando report {report_name}: {e}")
            else:
                logger.error(f"❌ Carpeta del reporte no encontrada: {report_folder}")
                print(f"⚠️ Carpeta del reporte no encontrada: {report_folder}")

        # Asegurar que la tabla de dependencias DAX siempre existe (aunque vacía)
        DaxTokenizer.ensure_dependencies_table(conn)

        # Analizar dependencias DAX de cada modelo semántico
        logger.info(f"🔍 Analizando dependencias DAX de medidas...")
        try:
            tk, measure_table_map = DaxTokenizer.from_duckdb(db_path, conn=conn)
            inserted = tk.save_dependencies_to_db(db_path, measure_table_map=measure_table_map, conn=conn)
            logger.info(f"✅ Dependencias DAX guardadas: {inserted} filas")
            print(f"📊 Dependencias DAX: {inserted} filas guardadas")
        except Exception as e:
            logger.error(f"❌ Error analizando dependencias DAX: {e}")
            print(f"⚠️ Error analizando dependencias DAX: {e}")

        # Guardar info actualizada
        os.makedirs(destination_path, exist_ok=True)
        with open(info_path, "w", encoding="utf-8") as f:
            json.dump(powerbiinfo, f, indent=2, ensure_ascii=False)

        # Cerrar conexión DuckDB
        conn.close()
        logger.info(f"✅ Base de datos DuckDB guardada en: {db_path}")
        logger.info(f"✅ Información del workspace guardada en: {info_path}")
        logger.info(f"✅ Importación del workspace '{workspace_name}' completada exitosamente")
        print(f"\n{'='*60}")
        print(f"✅ IMPORTACIÓN COMPLETADA")
        print(f"{'='*60}")
        print(f"📁 Archivos descargados en: {destination_path}")
        print(f"💾 Base de datos: {os.path.abspath(db_path)}")
        print(f"📊 Modelos semánticos: {len(ws_entry['semantic_models'])}")
        print(f"📋 Reportes: {len(ws_entry['reports'])}")
        print(f"{'='*60}\n")




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

