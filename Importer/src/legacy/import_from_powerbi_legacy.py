"""Funciones legacy no conectadas al flujo activo del importador Power BI.

Este módulo conserva utilidades históricas que actualmente no se usan
desde `mcp_server.py` ni desde el flujo principal de `import_from_powerbi.py`.
"""

import logging
import requests
from pathlib import Path


logger = logging.getLogger(__name__)


def get_data_path(data_path: Path) -> Path:
    """Devuelve la ruta de datos configurada externamente."""
    return data_path


def powerbi_download_report(get_authenticated_downloader, workspace_id: str, report_id: str, output_folder: str = "data"):
    """Descarga un reporte de Power BI usando un proveedor de downloader autenticado."""
    downloader = get_authenticated_downloader()
    if not downloader:
        return {"success": False, "message": "⚠️ No estás autenticado. Ejecuta powerbi_login_interactive primero."}

    try:
        downloader.download(workspace_id, report_id, output_folder)
        return {"success": True, "message": f"✅ Reporte descargado exitosamente en {output_folder}"}
    except Exception as e:
        return {"success": False, "message": f"❌ Error descargando reporte: {str(e)}"}


def powerbi_download_semantic_model(
    get_authenticated_downloader,
    workspace_id: str,
    semantic_model_id: str,
    output_folder: str = "data",
):
    """Descarga un modelo semántico de Power BI usando un downloader autenticado."""
    downloader = get_authenticated_downloader()
    if not downloader:
        return {"success": False, "message": "⚠️ No estás autenticado. Ejecuta powerbi_login_interactive primero."}

    try:
        downloader.download_semantic_model(workspace_id, semantic_model_id, output_folder)
        return {"success": True, "message": f"✅ Modelo semántico descargado exitosamente en {output_folder}"}
    except Exception as e:
        return {"success": False, "message": f"❌ Error descargando modelo semántico: {str(e)}"}


def execute_dax(fabric_item_downloader, dataset_id: str, payload: dict):
    """Ejecuta una query DAX contra un dataset en Power BI."""
    try:
        headers = {
            "Authorization": f"Bearer {fabric_item_downloader.access_token}",
            "Content-Type": "application/json",
        }

        url = f"https://api.powerbi.com/v1.0/myorg/datasets/{dataset_id}/executeQueries"
        response = requests.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code != 200:
            logger.warning(f"⚠️ Error execute_dax (código {response.status_code}): {response.text[:200]}")
            return None

        return response

    except Exception as e:
        logger.warning(f"⚠️ Error ejecutando DAX: {str(e)}")
        return None


def get_calc_dependencies_paginated(fabric_item_downloader, dataset_id: str, dataset_name: str, max_pages: int = 20):
    """Consulta dependencias de cálculo de un dataset con paginación."""
    all_rows = []
    page = 0
    continue_pagination = True

    dax_query = """
        SELECT
            *
        FROM
            $SYSTEM.DISCOVER_CALC_DEPENDENCY
    """

    while continue_pagination and page < max_pages:
        page_dax = dax_query.replace("{page_num}", str(page))

        payload = {
            "queries": [
                {
                    "query": page_dax
                }
            ],
            "serializerSettings": {
                "includeNulls": True
            }
        }

        response = execute_dax(fabric_item_downloader, dataset_id, payload)

        if not response:
            logger.warning(f"⚠️ Fallo obteniendo página {page} de dependencias para {dataset_name}")
            break

        try:
            data = response.json()
            rows = data.get("results", [{}])[0].get("tables", [{}])[0].get("rows", [])

            if not rows:
                logger.info(f"✅ Paginación completada para {dataset_name}: {page} página(s)")
                continue_pagination = False
            else:
                all_rows.extend(rows)
                page += 1
                logger.info(f"📄 Página {page} de {dataset_name}: {len(rows)} filas obtenidas")

        except Exception as e:
            logger.warning(f"⚠️ Error parseando respuesta DAX página {page}: {str(e)}")
            break

    return all_rows


def save_calc_dependencies_to_db(connection, workspace_id: str, calc_deps: list, semantic_models: list):
    """Guarda datos de DISCOVER_CALC_DEPENDENCIES en DuckDB."""
    if not calc_deps:
        return

    connection.execute("""
        CREATE TABLE IF NOT EXISTS calc_dependencies_workspace (
            id INTEGER PRIMARY KEY DEFAULT nextval('seq_calc_dep_id'),
            workspace_id VARCHAR NOT NULL,
            semantic_model_id VARCHAR,
            database_name VARCHAR,
            object_name VARCHAR,
            object_type VARCHAR,
            referenced_object_name VARCHAR,
            referenced_object_type VARCHAR,
            referenced_database_name VARCHAR,
            expression_text TEXT,
            calc_dependency_type VARCHAR,
            created_at TIMESTAMP DEFAULT now()
        )
    """)

    connection.execute("CREATE SEQUENCE IF NOT EXISTS seq_calc_dep_id START 1")

    model_name_to_id = {m["name"]: m["id"] for m in semantic_models}

    for row in calc_deps:
        database_name = row.get("DATABASE_NAME") or row.get("database_name", "")
        semantic_model_id = model_name_to_id.get(database_name)

        connection.execute("""
            INSERT INTO calc_dependencies_workspace
            (workspace_id, semantic_model_id, database_name, object_name, object_type,
             referenced_object_name, referenced_object_type, referenced_database_name,
             expression_text, calc_dependency_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            workspace_id,
            semantic_model_id,
            row.get("DATABASE_NAME") or row.get("database_name"),
            row.get("OBJECT_NAME") or row.get("object_name"),
            row.get("OBJECT_TYPE") or row.get("object_type"),
            row.get("REFERENCED_OBJECT_NAME") or row.get("referenced_object_name"),
            row.get("REFERENCED_OBJECT_TYPE") or row.get("referenced_object_type"),
            row.get("REFERENCED_DATABASE_NAME") or row.get("referenced_database_name"),
            row.get("EXPRESSION_TEXT") or row.get("expression_text", ""),
            row.get("CALC_DEPENDENCY_TYPE") or row.get("calc_dependency_type")
        ])

    print(f"✅ Guardadas {len(calc_deps)} filas de DISCOVER_CALC_DEPENDENCIES")
