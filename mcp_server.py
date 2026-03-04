#!/usr/bin/env python3
"""
MCP Server para gestión de modelos semánticos de Power BI
Expone herramientas para crear, analizar y optimizar modelos mediante lenguaje natural
"""

import asyncio
import json
from pathlib import Path
from typing import Any, List, Optional
from collections import defaultdict

from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

from models import SemanticModel, clsReport
from models.report import Page


# Configuración
MODELS_PATH = Path(__file__).parent / "Modelos"


class PowerBIModelServer:
    """Servidor MCP para gestión de modelos semánticos de Power BI"""

    async def _powerbi_login_interactive(self) -> list[TextContent]:
        """Inicia el login interactivo a Power BI y devuelve el link y el código para autenticarse."""
        try:
            from Importer.src.import_from_powerbi import start_device_flow_interactive, set_data_path
            # Configurar la ruta de datos
            set_data_path(str(self.data_path))
        except Exception as e:
            return [TextContent(type="text", text=f"Error importando módulo de login: {e}")]

        try:
            result = start_device_flow_interactive()
            
            if not result["success"]:
                return [TextContent(type="text", text=f"❌ Error iniciando login: {result['message']}")]
            
            if result.get("already_authenticated"):
                return [TextContent(type="text", text=f"✅ {result['message']}")]
            
            # Formatear el mensaje para que sea más claro
            message = result["message"]
            return [TextContent(type="text", text=f"🔐 Para autenticarte en Power BI:\n\n{message}\n\n⚠️ IMPORTANTE: Abre el enlace en tu navegador e introduce el código. La autenticación se completará automáticamente en segundo plano.")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error durante el login interactivo: {e}")]

    async def _powerbi_check_auth_status(self) -> list[TextContent]:
        """Verifica el estado de la autenticación de Power BI."""
        try:
            from Importer.src.import_from_powerbi import check_auth_status
        except Exception as e:
            return [TextContent(type="text", text=f"Error importando módulo: {e}")]

        try:
            result = check_auth_status()
            
            if result["authenticated"]:
                return [TextContent(type="text", text=f"✅ {result['message']}")]
            else:
                return [TextContent(type="text", text=f"⏳ {result['message']}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error verificando estado: {e}")]

    async def _powerbi_logout(self) -> list[TextContent]:
        """Cierra la sesión actual borrando el token de autenticación.
        Esto permite conectarse a otro tenant.
        Limpia tanto archivos como variables globales en memoria.
        """
        try:
            # Importar la variable global para limpiarla
            from Importer.src import import_from_powerbi
            
            files_deleted = []
            
            # Borrar archivo de token
            token_file = Path(__file__).parent / "fabric_token_cache.json"
            if token_file.exists():
                token_file.unlink()
                files_deleted.append("fabric_token_cache.json")
            
            # Borrar archivo de estado de autenticación
            status_file = Path(__file__).parent / "data" / "powerbi_auth_status.json"
            if status_file.exists():
                status_file.unlink()
                files_deleted.append("powerbi_auth_status.json")
            
            # Limpiar variable global _active_auth_flow
            import_from_powerbi._active_auth_flow = {
                "downloader": None, 
                "flow": None, 
                "message": None, 
                "thread": None,
                "status": None,
                "app": None
            }
            
            if files_deleted:
                return [TextContent(type="text", text=f"✅ Sesión cerrada correctamente.\n\n📄 Archivos eliminados:\n• {chr(10).join(files_deleted)}\n\n💾 Estado en memoria limpiado.\n\nAhora puedes conectarte a otro tenant usando 'powerbi_login_interactive'.")]
            else:
                return [TextContent(type="text", text=f"ℹ️ No hay sesión activa. Se limpió cualquier estado residual en memoria.\n\nPuedes iniciar sesión en otro tenant con 'powerbi_login_interactive'.")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error al cerrar sesión: {e}")]

    async def _powerbi_list_workspaces(self) -> list[TextContent]:
        """Lista todos los workspaces de Power BI disponibles."""
        try:
            from Importer.src.import_from_powerbi import powerbi_list_workspaces
        except Exception as e:
            return [TextContent(type="text", text=f"Error importando módulo: {e}")]

        try:
            result = powerbi_list_workspaces()
            
            if not result["success"]:
                return [TextContent(type="text", text=result["message"])]
            
            workspaces = result["workspaces"]
            output = f"🏢 Workspaces disponibles ({len(workspaces)}):\n\n"
            for ws in workspaces:
                output += f"• {ws.get('displayName', ws.get('name', 'N/A'))}\n"
                output += f"  ID: {ws['id']}\n\n"
            
            return [TextContent(type="text", text=output)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error listando workspaces: {e}")]

    async def _powerbi_list_reports(self, workspace_id: str) -> list[TextContent]:
        """Lista reportes con 3 comportamientos:
        1. Si está autenticado en Power BI → usa API
        2. Si hay BD predeterminada → lista desde BD
        3. Si no → informa al usuario
        """
        try:
            from Importer.src.import_from_powerbi import check_auth_status, powerbi_list_reports
        except Exception as e:
            return [TextContent(type="text", text=f"Error importando módulo: {e}")]

        # 1. Verificar si hay autenticación Power BI
        try:
            auth_result = check_auth_status()
            if auth_result.get("authenticated"):
                # Usar API de Power BI
                try:
                    result = powerbi_list_reports(workspace_id)
                    if not result["success"]:
                        return [TextContent(type="text", text=result["message"])]
                    
                    reports = result["reports"]
                    output = f"📊 Reportes en el workspace (desde Power BI API) ({len(reports)}):\n\n"
                    for rep in reports:
                        output += f"• {rep.get('displayName', rep.get('name', 'N/A'))}\n"
                        output += f"  ID: {rep['id']}\n\n"
                    
                    return [TextContent(type="text", text=output)]
                except Exception as e:
                    return [TextContent(type="text", text=f"Error usando API: {e}")]
        except Exception:
            pass
        
        # 2. Si no está autenticado, intentar usar BD predeterminada
        success, reports, error = self._get_reports_from_db()
        if success:
            output = f"📊 Reportes en el workspace (desde DuckDB) ({len(reports)}):\n\n"
            output += f"📁 Base de datos: {self.default_db_path}\n\n"
            for report_id, name, report_id_col, workspace_id_col in reports:
                output += f"• {name}\n"
                output += f"  ID: {report_id}\n\n"
            return [TextContent(type="text", text=output)]
        
        # 3. Si no hay BD ni autenticación, mostrar mensaje de ayuda
        return [TextContent(
            type="text",
            text=f"❌ No se puede listar reportes\n\n"
                 f"Tienes 2 opciones:\n\n"
                 f"1️⃣ **Autenticar en Power BI:**\n"
                 f"   Usa 'powerbi_login_interactive' para iniciar la autenticación\n\n"
                 f"2️⃣ **Usar una base de datos local:**\n"
                 f"   Usa 'default_db' para seleccionar una base de datos DuckDB descargada\n"
                 f"   BD actual: {self.default_db_path}\n\n"
                 f"Error: {error}"
        )]

    async def _powerbi_list_semantic_models(self, workspace_id: str) -> list[TextContent]:
        """Lista modelos semánticos con 3 comportamientos:
        1. Si está autenticado en Power BI → usa API
        2. Si hay BD predeterminada → lista desde BD
        3. Si no → informa al usuario
        """
        try:
            from Importer.src.import_from_powerbi import check_auth_status, powerbi_list_semantic_models
        except Exception as e:
            return [TextContent(type="text", text=f"Error importando módulo: {e}")]

        # 1. Verificar si hay autenticación Power BI
        try:
            auth_result = check_auth_status()
            if auth_result.get("authenticated"):
                # Usar API de Power BI
                try:
                    result = powerbi_list_semantic_models(workspace_id)
                    if not result["success"]:
                        return [TextContent(type="text", text=result["message"])]
                    
                    models = result["models"]
                    output = f"📦 Modelos semánticos en el workspace (desde Power BI API) ({len(models)}):\n\n"
                    for model in models:
                        output += f"• {model.get('displayName', model.get('name', 'N/A'))}\n"
                        output += f"  ID: {model['id']}\n\n"
                    
                    return [TextContent(type="text", text=output)]
                except Exception as e:
                    return [TextContent(type="text", text=f"Error usando API: {e}")]
        except Exception:
            pass
        
        # 2. Si no está autenticado, intentar usar BD predeterminada
        success, models, error = self._get_semantic_models_from_db()
        if success:
            output = f"📦 Modelos semánticos en el workspace (desde DuckDB) ({len(models)}):\n\n"
            output += f"📁 Base de datos: {self.default_db_path}\n\n"
            for model_id, semantic_model_id, workspace_id_col, name in models:
                output += f"• {name}\n"
                output += f"  ID: {model_id}\n\n"
            return [TextContent(type="text", text=output)]
        
        # 3. Si no hay BD ni autenticación, mostrar mensaje de ayuda
        return [TextContent(
            type="text",
            text=f"❌ No se puede listar modelos semánticos\n\n"
                 f"Tienes 2 opciones:\n\n"
                 f"1️⃣ **Autenticar en Power BI:**\n"
                 f"   Usa 'powerbi_login_interactive' para iniciar la autenticación\n\n"
                 f"2️⃣ **Usar una base de datos local:**\n"
                 f"   Usa 'default_db' para seleccionar una base de datos DuckDB descargada\n"
                 f"   BD actual: {self.default_db_path}\n\n"
                 f"Error: {error}"
        )]

    async def _powerbi_download_workspace(self, workspace_name: str, destination_path: str = None, db_name: str = "powerbi") -> list[TextContent]:
        """Descarga un workspace completo de Power BI (modelos semánticos y reportes)."""
        import os
        import traceback
        import logging
        
        # Usar data_path configurada si no se especifica destination_path
        if destination_path is None:
            destination_path = str(self.data_path)
        
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"🚀 Iniciando descarga de workspace: {workspace_name}")
            logger.info(f"📁 Directorio actual: {os.getcwd()}")
            logger.info(f"📁 Destino: {os.path.abspath(destination_path)}")
            logger.info(f"💾 BD: {db_name}")
            logger.info(f"{'='*60}")
            
            from Importer.src.import_from_powerbi import PowerBIImporter, _active_auth_flow
        except Exception as e:
            error_msg = f"Error importando módulo: {e}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return [TextContent(type="text", text=f"❌ {error_msg}")]

        try:
            # Obtener el downloader del flujo activo
            if not _active_auth_flow.get("downloader"):
                error_msg = "❌ No hay autenticación activa. Ejecuta 'powerbi_login_interactive' primero."
                logger.error(error_msg)
                return [TextContent(type="text", text=error_msg)]
            
            downloader = _active_auth_flow["downloader"]
            logger.info(f"✅ Downloader obtenido")
            logger.info(f"🔐 Token disponible: {bool(downloader.access_token)}")
            
            # Crear importer
            logger.info(f"📦 Creando PowerBIImporter para workspace: {workspace_name}")
            importer = PowerBIImporter(downloader, workspace_name=workspace_name)
            
            # Ejecutar importación
            logger.info(f"⏳ Ejecutando import_from_powerbi...")
            result = importer.import_from_powerbi(
                destination_path=destination_path,
                WorkspaceName=workspace_name,
                db_name=db_name
            )
            
            logger.info(f"✅ Importación completada")
            return [TextContent(type="text", text=f"✅ Workspace '{workspace_name}' descargado e importado exitosamente\n\n📁 Archivos descargados en: {os.path.abspath(destination_path)}\n💾 BD metainformación: {db_name}.duckdb\n\n⚠️ Revisa los logs para detalles de la importación")]
            
        except Exception as e:
            error_msg = f"❌ Error descargando workspace: {e}\n\n{traceback.format_exc()}"
            logger.error(error_msg)
            return [TextContent(type="text", text=f"{error_msg}\n\n💡 Verifica que:\n- El nombre del workspace sea correcto\n- Tengas permisos para acceder al workspace\n- La autenticación sea válida")]

    def __init__(self, models_path: Path, data_path: str = "D:/mcpdata"):
        self.models_path = models_path
        self.data_path = Path(data_path)  # Ruta configurable para datos, caché y BD
        self.server = Server("powerbi-semantic-model")
        self.default_db_name = "demostracion"
        self.default_db_path = self.data_path / "demostracion.duckdb"
        self._register_handlers()
    
    def _register_handlers(self):
        """Registra todos los manejadores de herramientas"""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """Lista todas las herramientas disponibles"""
            return [
                Tool(
                    name="set_models_path",
                    description="Cambia el directorio base donde se buscan modelos (.SemanticModel) y reportes (.Report)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Ruta absoluta o relativa al directorio que contiene modelos y reportes"
                            }
                        },
                        "required": ["path"]
                    }
                ), Tool(
                                        name="powerbi_login_interactive",
                                        description="Inicia el login interactivo a Power BI (device code flow) y devuelve el link y el código para autenticarse. Es necesario completar este paso antes de importar modelos desde Power BI.",
                                        inputSchema={
                                            "type": "object",
                                            "properties": {},
                                        }
                                    ),
                Tool(
                    name="powerbi_check_auth_status",
                    description="Verifica el estado de la autenticación de Power BI. Usa este comando para confirmar que el login se completó exitosamente.",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    }
                ),
                Tool(
                    name="powerbi_logout",
                    description="Cierra la sesión actual y borra el token de autenticación. Necesario para conectarse a otro tenant.",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    }
                ),
                Tool(
                    name="powerbi_list_workspaces",
                    description="Lista todos los workspaces de Power BI disponibles para el usuario autenticado.",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    }
                ),
                Tool(
                    name="powerbi_list_reports",
                    description="Lista todos los reportes de un workspace específico de Power BI.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workspace_id": {
                                "type": "string",
                                "description": "ID del workspace de Power BI"
                            }
                        },
                        "required": ["workspace_id"]
                    }
                ),
                Tool(
                    name="powerbi_list_semantic_models",
                    description="Lista todos los modelos semánticos de un workspace específico de Power BI.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workspace_id": {
                                "type": "string",
                                "description": "ID del workspace de Power BI"
                            }
                        },
                        "required": ["workspace_id"]
                    }
                ),
                Tool(
                    name="powerbi_download_workspace",
                    description="Descarga un workspace completo de Power BI (todos los modelos semánticos y reportes) a la ruta configurada en el MCP.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workspace_name": {
                                "type": "string",
                                "description": "Nombre del workspace a descargar"
                            },
                            "destination_path": {
                                "type": "string",
                                "description": "Ruta donde guardar los archivos descargados (default: ruta configurada en MCP, ej: D:/mcpdata)"
                            },
                            "db_name": {
                                "type": "string",
                                "description": "Nombre de la base de datos DuckDB para guardar metainformación (default: 'powerbi')",
                                "default": "powerbi"
                            }
                        },
                        "required": ["workspace_name"]
                    }
                ),
                Tool(
                    name="get_model_info",
                    description="Obtiene información detallada de un modelo semántico (tablas, relaciones, culturas)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "model_name": {
                                "type": "string",
                                "description": "Nombre del modelo (ej: FullAdventureWorks.SemanticModel)"
                            }
                        },
                        "required": ["model_name"]
                    }
                ),
                Tool(
                    name="analyze_report",
                    description="Analiza un reporte y extrae todas las referencias a tablas y columnas que usa",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "report_name": {
                                "type": "string",
                                "description": "Nombre del reporte (ej: FullAdventureWorks.Report)"
                            }
                        },
                        "required": ["report_name"]
                    }
                ),
                Tool(
                    name="get_report_pages",
                    description="Lista todas las páginas de un reporte con sus visuales",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "report_name": {
                                "type": "string",
                                "description": "Nombre del reporte (ej: FullAdventureWorks.Report)"
                            }
                        },
                        "required": ["report_name"]
                    }
                ),
                Tool(
                    name="get_page_visuals",
                    description="Obtiene los visuales de una página específica de un reporte",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "report_name": {
                                "type": "string",
                                "description": "Nombre del reporte"
                            },
                            "page_name": {
                                "type": "string",
                                "description": "Nombre o displayName de la página"
                            }
                        },
                        "required": ["report_name", "page_name"]
                    }
                ),
                Tool(
                    name="generate_report_svg",
                    description="Genera una visualización SVG de una página de reporte mostrando la disposición de todos los visuales",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "report_name": {
                                "type": "string",
                                "description": "Nombre del reporte"
                            },
                            "page_name": {
                                "type": "string",
                                "description": "Nombre o displayName de la página (opcional, usa la primera página si no se especifica)"
                            },
                            "save_to_file": {
                                "type": "boolean",
                                "description": "Si es true, guarda el SVG en un archivo además de devolverlo",
                                "default": False
                            }
                        },
                        "required": ["report_name"]
                    }
                ),
                Tool(
                    name="create_subset_model",
                    description="Crea un submodelo a partir de un modelo base, incluyendo solo las tablas especificadas y sus relaciones",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "source_model": {
                                "type": "string",
                                "description": "Nombre del modelo fuente"
                            },
                            "target_model": {
                                "type": "string",
                                "description": "Nombre del nuevo modelo a crear"
                            },
                            "tables": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Lista de nombres de tablas a incluir"
                            },
                            "search_direction": {
                                "type": "string",
                                "enum": ["ManyToOne", "OneToMany", "Both"],
                                "description": "Dirección de búsqueda de relaciones (por defecto: ManyToOne)",
                                "default": "ManyToOne"
                            },
                            "recursive": {
                                "type": "boolean",
                                "description": "Buscar recursivamente tablas relacionadas",
                                "default": True
                            },
                            "max_depth": {
                                "type": "integer",
                                "description": "Profundidad máxima de búsqueda recursiva",
                                "default": 3
                            }
                        },
                        "required": ["source_model", "target_model", "tables"]
                    }
                ),
                Tool(
                    name="create_model_from_reports",
                    description="Crea un modelo optimizado que incluye SOLO las tablas y columnas usadas en los reportes especificados",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "source_model": {
                                "type": "string",
                                "description": "Nombre del modelo fuente"
                            },
                            "target_model": {
                                "type": "string",
                                "description": "Nombre del nuevo modelo a crear"
                            },
                            "reports": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Lista de reportes a analizar (si está vacío, analiza todos)"
                            },
                            "include_related": {
                                "type": "boolean",
                                "description": "Incluir tablas relacionadas necesarias para integridad",
                                "default": False
                            }
                        },
                        "required": ["source_model", "target_model"]
                    }
                ),
                Tool(
                    name="get_table_details",
                    description="Obtiene detalles de una tabla específica (columnas, medidas, particiones)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "model_name": {
                                "type": "string",
                                "description": "Nombre del modelo"
                            },
                            "table_name": {
                                "type": "string",
                                "description": "Nombre de la tabla"
                            }
                        },
                        "required": ["model_name", "table_name"]
                    }
                ),
                Tool(
                    name="analyze_model_usage",
                    description="Analiza qué tablas/columnas de un modelo se usan en reportes",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "model_name": {
                                "type": "string",
                                "description": "Nombre del modelo a analizar"
                            }
                        },
                        "required": ["model_name"]
                    }
                ),
                Tool(
                    name="analyze_model_usage_bd",
                    description="Analiza uso del modelo usando DuckDB (report, report_column_used, report_measure_used)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "model_name": {
                                "type": "string",
                                "description": "Nombre del modelo a analizar"
                            },
                            "db_path": {
                                "type": "string",
                                "description": "Ruta a la base DuckDB (default: la configurada con default_db)"
                            },
                            "semantic_model_id": {
                                "type": "string",
                                "description": "GUID del modelo semántico (si no está en el objeto)"
                            }
                        },
                        "required": ["model_name"]
                    }
                ),
                Tool(
                    name="default_db",
                    description="Establece la base de datos DuckDB por defecto (ruta y nombre)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "db_path": {
                                "type": "string",
                                "description": "Ruta a la base DuckDB"
                            },
                            "db_name": {
                                "type": "string",
                                "description": "Nombre lógico de la base de datos"
                            }
                        },
                        "required": ["db_path", "db_name"]
                    }
                ),
                Tool(
                    name="querydb",
                    description="Ejecuta una consulta SQL en la base de datos DuckDB predeterminada",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Consulta SQL a ejecutar en DuckDB"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="generate_report_documentation",
                    description="Genera documentación HTML completa de un informe Power BI (o de todos) desde la BD DuckDB. "
                                "Incluye: cabecera, KPIs, informes asociados, detalle por página con SVG mockup, "
                                "tablas/columnas/métricas por página, código DAX de métricas, e inventario de tablas con código M. "
                                "Los ficheros HTML se guardan en la carpeta output dentro del directorio configurado con set_models_path.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "report_name": {
                                "type": "string",
                                "description": "Nombre del informe a documentar (tal como aparece en la BD). Si no se indica, se generan todos."
                            }
                        },
                        "required": []
                    }
                ),
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            """Ejecuta una herramienta"""
            
            if name == "set_models_path":
                return await self._set_models_path(arguments["path"])

            if name == "powerbi_login_interactive":
                return await self._powerbi_login_interactive()
            
            if name == "powerbi_check_auth_status":
                return await self._powerbi_check_auth_status()
            
            if name == "powerbi_logout":
                return await self._powerbi_logout()
            
            if name == "powerbi_list_workspaces":
                return await self._powerbi_list_workspaces()
            
            if name == "powerbi_list_reports":
                return await self._powerbi_list_reports(arguments["workspace_id"])
            
            if name == "powerbi_list_semantic_models":
                return await self._powerbi_list_semantic_models(arguments["workspace_id"])
            
            if name == "powerbi_download_workspace":
                return await self._powerbi_download_workspace(
                    arguments["workspace_name"],
                    arguments.get("destination_path", "data"),
                    arguments.get("db_name", "powerbi")
                )
            
            elif name == "get_model_info":
                return await self._get_model_info(arguments["model_name"])
            
            elif name == "analyze_report":
                return await self._analyze_report(arguments["report_name"])
            
            elif name == "get_report_pages":
                return await self._get_report_pages(arguments["report_name"])
            
            elif name == "get_page_visuals":
                return await self._get_page_visuals(
                    arguments["report_name"],
                    arguments["page_name"]
                )
            
            elif name == "generate_report_svg":
                return await self._generate_report_svg(
                    arguments["report_name"],
                    arguments.get("page_name"),
                    arguments.get("save_to_file", False)
                )
            
            elif name == "create_subset_model":
                return await self._create_subset_model(
                    arguments["source_model"],
                    arguments["target_model"],
                    arguments["tables"],
                    arguments.get("search_direction", "ManyToOne"),
                    arguments.get("recursive", True),
                    arguments.get("max_depth", 3),
                    arguments.get("create_pbip", True)
                )
            
            elif name == "create_model_from_reports":
                return await self._create_model_from_reports(
                    arguments["source_model"],
                    arguments["target_model"],
                    arguments.get("reports", []),
                    arguments.get("include_related", False),
                    arguments.get("copy_reports", True)
                )
            
            elif name == "get_table_details":
                return await self._get_table_details(
                    arguments["model_name"],
                    arguments["table_name"]
                )
            
            elif name == "analyze_model_usage":
                return await self._analyze_model_usage(arguments["model_name"])

            elif name == "analyze_model_usage_bd":
                return await self._analyze_model_usage_bd(
                    arguments["model_name"],
                    arguments.get("db_path"),
                    arguments.get("semantic_model_id")
                )

            elif name == "default_db":
                return await self._default_db(
                    arguments["db_path"],
                    arguments["db_name"]
                )
            
            elif name == "querydb":
                return await self._query_db(arguments["query"])
            
            elif name == "generate_report_documentation":
                return await self._generate_report_documentation(
                    arguments.get("report_name")
                )
            
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    def _get_workspace_path(self) -> Path:
        """Obtiene la ruta del directorio de workspace basado en default_db_name.
        
        Retorna: self.data_path / self.default_db_name
        Ej: D:/mcpdata/demostracion para default_db_name = "demostracion"
        """
        return self.data_path / self.default_db_name
    
    def _get_reports_from_db(self) -> tuple[bool, list, str]:
        """Intenta consultar reportes desde la BD predeterminada.
        
        Returns:
            (success: bool, reports: list, message: str)
        """
        if not self.default_db_path.exists():
            return False, [], f"BD no encontrada: {self.default_db_path}"
        
        try:
            import duckdb
            connection = duckdb.connect(str(self.default_db_path), read_only=True)
            reports = connection.execute("SELECT id, name, report_id, workspace_id FROM report ORDER BY name").fetchall()
            connection.close()
            return True, reports, ""
        except Exception as e:
            return False, [], str(e)
    
    def _get_semantic_models_from_db(self) -> tuple[bool, list, str]:
        """Intenta consultar modelos semánticos desde la BD predeterminada.
        
        Returns:
            (success: bool, models: list, message: str)
        """
        if not self.default_db_path.exists():
            return False, [], f"BD no encontrada: {self.default_db_path}"
        
        try:
            import duckdb
            connection = duckdb.connect(str(self.default_db_path), read_only=True)
            models = connection.execute("SELECT id, semantic_model_id, workspace_id, name FROM semantic_model ORDER BY name").fetchall()
            connection.close()
            return True, models, ""
        except Exception as e:
            return False, [], str(e)
    
    async def _generate_report_documentation(self, report_name: str = None) -> list[TextContent]:
        """Genera documentación HTML de informe(s) Power BI desde DuckDB.
        
        Guarda los HTML en self.models_path / 'output'.
        Si report_name es None, genera para todos los informes.
        """
        if not self.default_db_path.exists():
            return [TextContent(type="text", text=(
                f"❌ No se encontró la base de datos: {self.default_db_path}\n\n"
                f"Configura la ruta con 'set_models_path' o 'default_db' primero."
            ))]

        try:
            import duckdb
            from scripts.documenta_report import generate_report_html, _get_all_report_names
        except ImportError as e:
            return [TextContent(type="text", text=f"❌ Error de importación: {e}")]

        output_dir = self.models_path / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            con = duckdb.connect(str(self.default_db_path), read_only=True)

            # Determinar informes a procesar
            if report_name:
                report_names = [report_name]
            else:
                report_names = _get_all_report_names(con)
                if not report_names:
                    con.close()
                    return [TextContent(type="text", text="No hay informes en la base de datos.")]

            generated = []
            errors = []
            generated_paths = set()

            for name in report_names:
                try:
                    html_output = generate_report_html(con, name)
                    safe_name = "".join(
                        c if c.isalnum() or c in " _-" else "_" for c in name
                    ).strip()
                    out_path = output_dir / f"{safe_name}.html"
                    # Desambiguar colisiones
                    counter = 2
                    while str(out_path) in generated_paths:
                        out_path = output_dir / f"{safe_name}_{counter}.html"
                        counter += 1
                    generated_paths.add(str(out_path))
                    out_path.write_text(html_output, encoding="utf-8")
                    generated.append((name, str(out_path)))
                except Exception as e:
                    errors.append((name, str(e)))

            con.close()

            # Formatear resultado
            result_parts = []
            result_parts.append(f"✅ Documentación generada: {len(generated)} informe(s)")
            result_parts.append(f"📁 Carpeta de salida: {output_dir}\n")

            if len(generated) <= 20:
                for rname, rpath in generated:
                    result_parts.append(f"  • {rname}  →  {rpath}")
            else:
                for rname, rpath in generated[:10]:
                    result_parts.append(f"  • {rname}  →  {rpath}")
                result_parts.append(f"  ... y {len(generated) - 10} más")

            if errors:
                result_parts.append(f"\n⚠️ Errores en {len(errors)} informe(s):")
                for rname, err in errors:
                    result_parts.append(f"  ✗ {rname}: {err}")

            return [TextContent(type="text", text="\n".join(result_parts))]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error generando documentación: {e}")]

    async def _set_models_path(self, path_str: str) -> list[TextContent]:
        """Actualiza el directorio base de modelos y reportes.
        
        También actualiza data_path, default_db_name y default_db_path
        para que apunten coherentemente a la nueva ubicación.
        """
        new_path = Path(path_str)
        # Permitir relativo al cwd donde corre el servidor
        if not new_path.is_absolute():
            new_path = (Path.cwd() / new_path).resolve()
        if not new_path.exists() or not new_path.is_dir():
            return [TextContent(type="text", text=f"Error: la ruta especificada no existe o no es un directorio: {new_path}")]

        self.models_path = new_path
        # Actualizar data_path al directorio padre y default_db_name al nombre de la carpeta
        self.data_path = new_path.parent
        self.default_db_name = new_path.name
        # Buscar un .duckdb en la carpeta padre que coincida con el nombre
        candidate_db = self.data_path / f"{self.default_db_name}.duckdb"
        if candidate_db.exists():
            self.default_db_path = candidate_db
        else:
            # Buscar cualquier .duckdb en data_path
            duckdb_files = list(self.data_path.glob("*.duckdb"))
            if duckdb_files:
                self.default_db_path = duckdb_files[0]
                self.default_db_name = duckdb_files[0].stem
            else:
                self.default_db_path = candidate_db  # mantener la ruta esperada aunque no exista
        
        return [TextContent(type="text", text=(
            f"✅ Directorio de modelos actualizado a: {self.models_path}\n"
            f"📁 Data path: {self.data_path}\n"
            f"💾 BD por defecto: {self.default_db_path}"
        ))]
    
    async def _get_model_info(self, model_name: str) -> list[TextContent]:
        """Obtiene información de un modelo del workspace actual"""
        workspace_path = self._get_workspace_path()
        model_path = workspace_path / model_name
        
        if not model_path.exists():
            return [TextContent(type="text", text=f"Error: Modelo '{model_name}' no encontrado en {workspace_path}")]
        
        # Cargar modelo
        model = SemanticModel(str(model_path))
        model.load_from_directory(model_path)
        
        # Generar resumen
        result = f"=== Información del Modelo: {model_name} ===\n\n"
        result += f"📊 Tablas: {len(model.tables)}\n"
        result += f"🔗 Relaciones: {len(model.relationships)}\n"
        result += f"🌍 Culturas: {len(model.cultures)}\n\n"
        
        result += "### Tablas:\n"
        for table in sorted(model.tables, key=lambda t: t.name):
            result += f"\n**{table.name}**\n"
            result += f"  - Columnas: {len(table.columns)}\n"
            result += f"  - Medidas: {len(table.measures)}\n"
            result += f"  - Particiones: {len(table.partitions)}\n"
        
        result += f"\n### Relaciones:\n"
        for rel in model.relationships[:10]:  # Primeras 10
            result += f"- {rel.from_table}.{rel.from_column} → {rel.to_table}.{rel.to_column}\n"
        
        if len(model.relationships) > 10:
            result += f"... y {len(model.relationships) - 10} más\n"
        
        return [TextContent(type="text", text=result)]
    
    async def _analyze_report(self, report_name: str) -> list[TextContent]:
        """Analiza un reporte del workspace actual"""
        workspace_path = self._get_workspace_path()
        report_path = workspace_path / report_name
        
        if not report_path.exists():
            return [TextContent(type="text", text=f"Error: Reporte '{report_name}' no encontrado en {workspace_path}")]
        
        # Parsear reporte
        report = clsReport(str(report_path))
        
        # Obtener referencias
        columns_refs = report.get_all_columns_used()
        measures_refs = report.get_all_measures_used()
        
        # Generar resumen
        result = f"=== Análisis del Reporte: {report_name} ==="
        
        total_fields = sum(len(cols) for cols in columns_refs.values()) + sum(len(meas) for meas in measures_refs.values())
        all_tables = set(list(columns_refs.keys()) + list(measures_refs.keys()))
        result += f"\n📊 Tablas usadas: {len(all_tables)}\n"
        result += f"📋 Campos totales: {total_fields}\n"
        result += f"📄 Páginas: {len(report.pages)}\n\n"
        
        # Mostrar columnas por tabla
        result += "\n=== COLUMNAS ===\n"
        for table in sorted(columns_refs.keys()):
            fields = sorted(columns_refs[table])
            result += f"\n### {table} ({len(fields)} columnas):\n"
            for field in fields:
                result += f"  - {field}\n"
        
        # Mostrar medidas por tabla
        if measures_refs:
            result += "\n=== MEDIDAS ===\n"
            for table in sorted(measures_refs.keys()):
                measures = sorted(measures_refs[table])
                result += f"\n### {table} ({len(measures)} medidas):\n"
                for measure in measures:
                    result += f"  - {measure}\n"
        
        return [TextContent(type="text", text=result)]
    
    async def _get_report_pages(self, report_name: str) -> list[TextContent]:
        """Lista todas las páginas de un reporte con información de visuales"""
        report_path = self.models_path / report_name
        
        if not report_path.exists():
            return [TextContent(type="text", text=f"Error: Reporte '{report_name}' no encontrado")]
        
        # Parsear reporte
        report = clsReport(str(report_path))
        
        # Generar listado de páginas
        result = f"=== Páginas del Reporte: {report_name} ===\n\n"
        result += f"Total de páginas: {len(report.pages)}\n\n"
        
        for i, page in enumerate(report.pages, 1):
            display_name = page.displayName if page.displayName else page.name
            result += f"{i}. **{display_name}**\n"
            result += f"   - Nombre: {page.name}\n"
            result += f"   - Visuales: {len(page.visuals)}\n"
            result += f"   - Dimensiones: {page.width}x{page.height}\n\n"
        
        return [TextContent(type="text", text=result)]
    
    async def _get_page_visuals(self, report_name: str, page_name: str) -> list[TextContent]:
        """Obtiene los visuales de una página específica"""
        report_path = self.models_path / report_name
        
        if not report_path.exists():
            return [TextContent(type="text", text=f"Error: Reporte '{report_name}' no encontrado")]
        
        # Parsear reporte
        report = clsReport(str(report_path))
        
        # Buscar página por nombre o displayName
        target_page = None
        for page in report.pages:
            if page.name == page_name or (page.displayName and page.displayName == page_name):
                target_page = page
                break
        
        if not target_page:
            return [TextContent(type="text", text=f"Error: Página '{page_name}' no encontrada en el reporte")]
        
        # Generar listado de visuales
        display_name = target_page.displayName if target_page.displayName else target_page.name
        result = f"=== Visuales de la Página: {display_name} ===\n\n"
        result += f"Total de visuales: {len(target_page.visuals)}\n\n"
        
        for i, visual in enumerate(target_page.visuals, 1):
            result += f"{i}. **{visual.name}**\n"
            result += f"   - Tipo: {visual.visualType}\n"
            result += f"   - Posición: x={visual.position['x']}, y={visual.position['y']}\n"
            result += f"   - Tamaño: {visual.position['width']}x{visual.position['height']}\n"
            
            # Columnas y medidas organizadas por tabla
            columns_by_table = defaultdict(set)
            measures_by_table = defaultdict(set)
            
            for col_ref in visual.columns_used:
                if '.' in col_ref:
                    table, col = col_ref.split('.', 1)
                    columns_by_table[table].add(col)
            
            for meas_ref in visual.measures_used:
                if '.' in meas_ref:
                    table, meas = meas_ref.split('.', 1)
                    measures_by_table[table].add(meas)
            
            if columns_by_table:
                total_cols = sum(len(cols) for cols in columns_by_table.values())
                result += f"   - Columnas ({total_cols}):\n"
                for table in sorted(columns_by_table.keys()):
                    for col in sorted(columns_by_table[table]):
                        result += f"     • {table}.{col}\n"
            
            if measures_by_table:
                total_meas = sum(len(meas) for meas in measures_by_table.values())
                result += f"   - Medidas ({total_meas}):\n"
                for table in sorted(measures_by_table.keys()):
                    for meas in sorted(measures_by_table[table]):
                        result += f"     • {table}.{meas}\n"
            
            result += "\n"
        
        return [TextContent(type="text", text=result)]
    
    def _generate_svg_from_db(self, report_name: str, page_name: Optional[str] = None) -> tuple[bool, Optional[object], str]:
        """Intenta generar SVG usando datos de DuckDB.
        
        Returns:
            (success, target_page, error_message)
        """
        if not self.default_db_path.exists():
            return False, None, "BD no disponible"
        
        try:
            import duckdb
            connection = duckdb.connect(str(self.default_db_path), read_only=True)
            
            # Buscar página en la BD
            if page_name:
                page_row = connection.execute(
                    "SELECT name, display_name, width, height FROM report_page WHERE report_name = ? AND (name = ? OR display_name = ?)",
                    [report_name, page_name, page_name]
                ).fetchone()
            else:
                page_row = connection.execute(
                    "SELECT name, display_name, width, height FROM report_page WHERE report_name = ? LIMIT 1",
                    [report_name]
                ).fetchone()
            
            if not page_row:
                connection.close()
                return False, None, f"Página no encontrada en DuckDB para reporte '{report_name}'"
            
            pg_name, pg_display_name, pg_width, pg_height = page_row
            
            # Obtener visuales de la página
            visuals_rows = connection.execute(
                """SELECT name, visual_type, position_x, position_y, position_width, position_height, text_content 
                   FROM report_visual 
                   WHERE report_name = ? AND page_name = ?""",
                [report_name, pg_name]
            ).fetchall()
            connection.close()
            
            # Construir Page ligera con los datos de la BD (sin leer del filesystem)
            from types import SimpleNamespace
            
            target_page = Page.__new__(Page)
            target_page.name = pg_name
            target_page.displayName = pg_display_name
            target_page.width = pg_width
            target_page.height = pg_height
            target_page.visuals = []
            
            for row in visuals_rows:
                v = SimpleNamespace(
                    name=row[0],
                    visualType=row[1],
                    position={
                        'x': row[2] or 0,
                        'y': row[3] or 0,
                        'width': row[4] or 200,
                        'height': row[5] or 160
                    },
                    text=row[6],
                    columns_used=[],
                    measures_used=[],
                    filters=[],
                    navigationTarget=None
                )
                target_page.visuals.append(v)
            
            return True, target_page, ""
        except Exception as e:
            return False, None, f"Error al consultar DuckDB: {e}"

    async def _generate_report_svg(self, report_name: str, page_name: Optional[str] = None, save_to_file: bool = False) -> list[TextContent]:
        """Genera una visualización SVG de una página de reporte.
        
        Primero intenta usar DuckDB para obtener los datos de la página y sus visuales.
        Si no hay BD disponible o el reporte no está en la BD, cae al sistema de archivos.
        """
        target_page = None
        source = "filesystem"
        
        # 1. Intentar desde DuckDB
        db_ok, db_page, db_msg = self._generate_svg_from_db(report_name, page_name)
        if db_ok and db_page:
            target_page = db_page
            source = "DuckDB"
        else:
            # 2. Fallback: leer del sistema de archivos
            report_path = self.models_path / report_name
            
            if not report_path.exists():
                return [TextContent(type="text", text=f"Error: Reporte '{report_name}' no encontrado ni en DuckDB ni en el filesystem.\nDuckDB: {db_msg}")]
            
            report = clsReport(str(report_path))
            
            if not report.pages:
                return [TextContent(type="text", text=f"Error: El reporte no tiene páginas")]
            
            if page_name:
                for page in report.pages:
                    if page.name == page_name or (page.displayName and page.displayName == page_name):
                        target_page = page
                        break
                if not target_page:
                    return [TextContent(type="text", text=f"Error: Página '{page_name}' no encontrada")]
            else:
                target_page = report.pages[0]
        
        # Generar SVG
        svg_content = target_page.generate_svg_page()
        
        # Guardar a archivo si se solicita
        if save_to_file:
            output_file = self.models_path / f"{report_name.replace('.Report', '')}_{target_page.name}.svg"
            output_file.write_text(svg_content, encoding='utf-8')
            
            display_name = target_page.displayName if target_page.displayName else target_page.name
            result = f"✅ SVG generado y guardado en:\n{output_file}\n\n"
            result += f"📊 Fuente de datos: {source}\n"
            result += f"Página: {display_name}\n"
            result += f"Visuales renderizados: {len(target_page.visuals)}\n"
            result += f"Tamaño del SVG: {len(svg_content)} caracteres\n\n"
            result += "--- Vista previa (primeros 500 caracteres) ---\n"
            result += svg_content[:500] + "..."
        else:
            display_name = target_page.displayName if target_page.displayName else target_page.name
            result = f"=== SVG de la Página: {display_name} ===\n\n"
            result += f"📊 Fuente de datos: {source}\n"
            result += f"Visuales renderizados: {len(target_page.visuals)}\n"
            result += f"Tamaño: {len(svg_content)} caracteres\n\n"
            result += svg_content
        
        return [TextContent(type="text", text=result)]
    
    async def _create_subset_model(
        self, 
        source_model: str, 
        target_model: str,
        tables: List[str],
        search_direction: str,
        recursive: bool,
        max_depth: int,
        create_pbip: bool
    ) -> list[TextContent]:
        """Crea un submodelo"""
        
        source_path = self.models_path / source_model
        if not source_path.exists():
            return [TextContent(type="text", text=f"Error: Modelo fuente '{source_model}' no encontrado")]
        
        # Cargar modelo fuente
        model = SemanticModel(str(source_path))
        model.load_from_directory(source_path)
        
        # Crear especificaciones de tablas
        table_specs = [(table, search_direction) for table in tables]
        
        # Crear submodelo (legacy: selección manual de tablas)
        subset = model.create_subset_model_legacy(
            table_specs=table_specs,
            subset_name=target_model,
            recursive=recursive,
            max_depth=max_depth
        )
        
        # Guardar
        target_path = self.models_path / target_model
        subset.save_to_directory(target_path)

        # Crear pbip + report vacío por defecto
        if create_pbip:
            await self._scaffold_empty_report_and_pbip(target_model)
        
        result = f"✅ Submodelo creado exitosamente: {target_model}\n\n"
        result += f"Tablas incluidas: {len(subset.tables)}\n"
        result += f"Relaciones: {len(subset.relationships)}\n\n"
        result += "Tablas:\n"
        for table in sorted(subset.tables, key=lambda t: t.name):
            result += f"  - {table.name} ({len(table.columns)} columnas, {len(table.measures)} medidas)\n"
        
        return [TextContent(type="text", text=result)]
    
    async def _create_model_from_reports(
        self,
        source_model: str,
        target_model: str,
        reports: List[str],
        include_related: bool,
        copy_reports: bool
    ) -> list[TextContent]:
        """Crea modelo basado en reportes usando datos de DuckDB.

        Utiliza ``create_subset_model_from_db`` que consulta las tablas
        ``report_column_used``, ``report_measure_used`` y
        ``semantic_model_measure_dependencies`` para determinar qué tablas,
        columnas, medidas y relaciones necesita el submodelo.
        """
        
        source_path = self.models_path / source_model
        if not source_path.exists():
            return [TextContent(type="text", text=f"Error: Modelo fuente '{source_model}' no encontrado")]
        
        db_path = str(self.default_db_path)

        # Cargar modelo fuente
        model = SemanticModel(str(source_path))
        model.load_from_directory(source_path)
        
        # Crear submodelo desde la base de datos
        subset = model.create_subset_model_from_db(
            db_path=db_path,
            subset_name=target_model,
        )
        
        # Guardar
        target_path = self.models_path / target_model
        subset.save_to_directory(target_path)

        # Si se solicita, copiar páginas de los reportes origen, acumulando
        if copy_reports:
            if not reports:
                reports = [d.name for d in self.models_path.iterdir()
                          if d.is_dir() and d.name.endswith('.Report')]
            await self._copy_and_merge_report_pages(
                source_reports=reports,
                target_report_name=self._derive_report_name_from_model(target_model)
            )
        
        result = f"✅ Modelo optimizado creado: {target_model}\n\n"
        result += f"Basado en datos de DuckDB ({db_path})\n"
        result += f"Tablas: {len(subset.tables)}\n"
        result += f"Relaciones: {len(subset.relationships)}\n\n"
        
        for table in sorted(subset.tables, key=lambda t: t.name):
            result += f"**{table.name}**\n"
            result += f"  - Columnas: {len(table.columns)}\n"
            result += f"  - Medidas: {len(table.measures)}\n"
        
        return [TextContent(type="text", text=result)]

    def _derive_report_name_from_model(self, model_name: str) -> str:
        """Convención: <Name>.SemanticModel -> <Name>.Report"""
        base = model_name.replace('.SemanticModel', '')
        return f"{base}.Report"

    async def _scaffold_empty_report_and_pbip(self, model_name: str) -> None:
        """Crea un .pbip y un .Report vacío enlazado al modelo."""
        SemanticModel.scaffold_pbip_and_report(self.models_path, model_name)

    async def _copy_and_merge_report_pages(self, source_reports: List[str], target_report_name: str) -> None:
        """Copia páginas de uno o varios reports origen y las acumula en el report destino.

        - Lee `definition/report.json` de cada report origen.
        - Concadena las entradas de `pages` en el `report.json` destino.
        - No copia StaticResources; solo estructura de páginas.
        - NO incluye la clave 'pages' en report.json si está vacía (Power BI Desktop requiere esto)
        """
        target_dir = self.models_path / target_report_name / "definition"
        target_report_json_path = target_dir / "report.json"
        if not target_report_json_path.exists():
            return

        # Cargar destino
        target_data = json.loads(target_report_json_path.read_text(encoding="utf-8"))

        # Acumular páginas
        for src in source_reports:
            src_dir = self.models_path / src / "definition"
            src_report_json_path = src_dir / "report.json"
            if not src_report_json_path.exists():
                # Si el report de origen no tiene report.json, simplemente ignorar
                continue
            try:
                src_data = json.loads(src_report_json_path.read_text(encoding="utf-8"))
                src_pages = src_data.get("pages", [])
                # Evitar duplicados simples por nombre
                existing_names = {p.get("name") for p in target_data.get("pages", [])}
                for p in src_pages:
                    name = p.get("name")
                    if name and name in existing_names:
                        # si existe, crear nombre único
                        suffix = 2
                        new_name = f"{name} ({suffix})"
                        while new_name in existing_names:
                            suffix += 1
                            new_name = f"{name} ({suffix})"
                        p = {**p, "name": new_name}
                        existing_names.add(new_name)
                        target_data["pages"].append(p)
                    else:
                        if name:
                            existing_names.add(name)
                        target_data["pages"].append(p)
            except Exception:
                # continuar si hay errores de formato
                continue

        # Guardar destino
        # IMPORTANTE: NO incluir 'pages' si está vacía (Power BI Desktop no abre archivos con pages: [])
        if "pages" in target_data and not target_data["pages"]:
            del target_data["pages"]
        
        target_report_json_path.write_text(json.dumps(target_data, indent=2), encoding="utf-8")
    
    async def _get_table_details(self, model_name: str, table_name: str) -> list[TextContent]:
        """Obtiene detalles de una tabla"""
        model_path = self.models_path / model_name
        
        if not model_path.exists():
            return [TextContent(type="text", text=f"Error: Modelo '{model_name}' no encontrado")]
        
        # Cargar modelo
        model = SemanticModel(str(model_path))
        model.load_from_directory(model_path)
        
        # Buscar tabla
        table = next((t for t in model.tables if t.name == table_name), None)
        if not table:
            return [TextContent(type="text", text=f"Error: Tabla '{table_name}' no encontrada")]
        
        result = f"=== Detalles de la Tabla: {table_name} ===\n\n"
        
        result += f"### Columnas ({len(table.columns)}):\n"
        for col in table.columns[:20]:  # Primeras 20
            result += f"- {col.name}"
            if col.data_type:
                result += f" ({col.data_type})"
            result += "\n"
        
        if len(table.columns) > 20:
            result += f"... y {len(table.columns) - 20} más\n"
        
        result += f"\n### Medidas ({len(table.measures)}):\n"
        for measure in table.measures:
            result += f"- {measure.name}"
            if measure.expression:
                # Mostrar expresión completa, formateada adecuadamente
                expr_lines = measure.expression.split('\n')
                if len(expr_lines) == 1:
                    result += f" = {measure.expression}"
                else:
                    result += " = \n```\n" + measure.expression + "\n```"
            result += "\n"
        
        result += f"\n### Particiones ({len(table.partitions)}):\n"
        for partition in table.partitions:
            result += f"\n**{partition.name}**\n"
            result += f"  - Tipo: {partition.source_type or 'N/A'}\n"
            result += f"  - Modo: {partition.mode or 'N/A'}\n"
            
            # Mostrar preview del código fuente
            if partition.source_expression:
                source_lines = partition.source_expression.split('\n')
                if len(source_lines) <= 5:
                    result += f"  - Source:\n```\n{partition.source_expression}\n```\n"
                else:
                    # Mostrar primeras 5 líneas
                    preview = '\n'.join(source_lines[:5])
                    result += f"  - Source (primeras 5 líneas):\n```\n{preview}\n... ({len(source_lines)} líneas totales)\n```\n"
        
        return [TextContent(type="text", text=result)]
    
    async def _analyze_model_usage(self, model_name: str) -> list[TextContent]:
        """Analiza uso del modelo en reportes"""
        
        # Buscar todos los reportes
        reports = [d for d in self.models_path.iterdir() 
                  if d.is_dir() and d.name.endswith('.Report')]
        
        # Analizar cada reporte
        usage = defaultdict(lambda: defaultdict(set))
        
        for report_dir in reports:
            report_obj = clsReport(str(report_dir))
            columns_refs = report_obj.get_all_columns_used()
            measures_refs = report_obj.get_all_measures_used()
            
            for table, fields in columns_refs.items():
                usage[table][report_dir.name].update(fields)
            for table, fields in measures_refs.items():
                usage[table][report_dir.name].update(fields)
        
        # Cargar modelo para comparar
        model_path = self.models_path / model_name
        if model_path.exists():
            model = SemanticModel(str(model_path))
            model.load_from_directory(model_path)
            
            result = f"=== Análisis de Uso: {model_name} ===\n\n"
            result += f"Total de tablas en el modelo: {len(model.tables)}\n"
            result += f"Tablas usadas en reportes: {len(usage)}\n"
            result += f"Tablas NO usadas: {len(model.tables) - len(usage)}\n\n"
            
            # Tablas usadas
            result += "### Tablas Usadas:\n"
            for table in sorted(usage.keys()):
                reports_using = usage[table]
                result += f"\n**{table}** (usado en {len(reports_using)} reportes):\n"
                for report, fields in reports_using.items():
                    result += f"  - {report}: {len(fields)} campos\n"
            
            # Tablas no usadas
            unused = [t.name for t in model.tables if t.name not in usage]
            if unused:
                result += f"\n### Tablas NO Usadas ({len(unused)}):\n"
                for table in sorted(unused):
                    result += f"- {table}\n"
        else:
            result = f"Error: Modelo '{model_name}' no encontrado"
        
        return [TextContent(type="text", text=result)]

    async def _analyze_model_usage_bd(
        self,
        model_name: str,
        db_path: Optional[str],
        semantic_model_id: Optional[str] = None
    ) -> list[TextContent]:
        """Analiza uso del modelo en reportes usando DuckDB."""
        model_path = self.models_path / model_name

        if not model_path.exists():
            return [TextContent(type="text", text=f"Error: Modelo '{model_name}' no encontrado")]

        model = SemanticModel(str(model_path), semantic_model_id=semantic_model_id)
        model.load_from_directory(model_path)
        if semantic_model_id:
            model.semantic_model_id = semantic_model_id

        if not model.semantic_model_id:
            return [TextContent(
                type="text",
                text=(
                    "Error: semantic_model_id no definido. "
                    "Proporciona 'semantic_model_id' o asegúrate de que el modelo lo tenga cargado."
                )
            )]

        if not db_path:
            db_path = str(self.default_db_path)

        try:
            import duckdb
            connection = duckdb.connect(db_path)
        except Exception as e:
            return [TextContent(type="text", text=f"Error abriendo DuckDB: {e}")]

        try:
            model.load_dependencies_from_db(connection)
        finally:
            try:
                connection.close()
            except Exception:
                pass

        used_tables = set(model.usage_by_table.keys())
        total_tables = len(model.tables)
        unused_tables = [t.name for t in model.tables if t.name not in used_tables]

        result = f"=== Análisis de Uso (DuckDB): {model_name} ===\n\n"
        result += f"DB: {db_path}\n"
        result += f"Reportes relacionados: {len(model.report_usage)}\n"
        result += f"Tablas usadas: {len(used_tables)}\n"
        result += f"Tablas NO usadas: {max(total_tables - len(used_tables), 0)}\n\n"

        if model.report_usage:
            result += "### Reportes:\n"
            for report in sorted(model.report_usage, key=lambda r: r["report_name"]):
                result += (
                    f"- {report['report_name']}: "
                    f"{report['total_column_usage']} columnas, "
                    f"{report['total_measure_usage']} medidas\n"
                )

        if used_tables:
            result += "\n### Tablas Usadas:\n"
            for table_name in sorted(used_tables):
                table_entry = model.usage_by_table.get(table_name, {})
                columns_count = sum(table_entry.get("columns", {}).values())
                measures_count = sum(table_entry.get("measures", {}).values())
                reports_count = len(table_entry.get("reports", []))
                result += (
                    f"- {table_name}: {columns_count} columnas, "
                    f"{measures_count} medidas, {reports_count} reportes\n"
                )

        if unused_tables:
            result += f"\n### Tablas NO Usadas ({len(unused_tables)}):\n"
            for table in sorted(unused_tables):
                result += f"- {table}\n"

        return [TextContent(type="text", text=result)]

    async def _default_db(self, db_path: str, db_name: str) -> list[TextContent]:
        """Actualiza la base DuckDB por defecto usada por el servidor."""
        new_path = Path(db_path)
        if not new_path.is_absolute():
            new_path = (Path.cwd() / new_path).resolve()

        self.default_db_path = new_path
        self.default_db_name = db_name

        return [TextContent(
            type="text",
            text=(
                f"✅ Base DuckDB por defecto actualizada:\n"
                f"- Nombre: {self.default_db_name}\n"
                f"- Ruta: {self.default_db_path}"
            )
        )]
    
    async def _query_db(self, query: str) -> list[TextContent]:
        """Ejecuta una consulta SQL en la BD DuckDB predeterminada.
        
        Args:
            query: Consulta SQL a ejecutar
            
        Returns:
            Resultados de la consulta en formato texto
        """
        if not self.default_db_path.exists():
            return [TextContent(
                type="text",
                text=f"❌ Base de datos no encontrada: {self.default_db_path}\n\n"
                     f"Usa 'default_db' para configurar una base de datos válida."
            )]
        
        try:
            import duckdb
            connection = duckdb.connect(str(self.default_db_path), read_only=True)
            
            # Ejecutar la consulta
            result = connection.execute(query).fetchall()
            columns = [desc[0] for desc in connection.description] if connection.description else []
            
            connection.close()
            
            # Formatear resultados
            if not result:
                return [TextContent(
                    type="text",
                    text=f"✅ Consulta ejecutada correctamente.\n\n"
                         f"No se devolvieron resultados."
                )]
            
            # Crear tabla con resultados
            output = f"✅ Consulta ejecutada correctamente.\n\n"
            output += f"📊 Resultados ({len(result)} filas):\n\n"
            
            # Encabezados
            if columns:
                output += "| " + " | ".join(columns) + " |\n"
                output += "|" + "|".join([" --- " for _ in columns]) + "|\n"
                
                # Filas
                for row in result:
                    output += "| " + " | ".join(str(val) for val in row) + " |\n"
            else:
                # Si no hay columnas conocidas, mostrar como JSON
                for row in result:
                    output += str(row) + "\n"
            
            return [TextContent(type="text", text=output)]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Error ejecutando consulta:\n\n{str(e)}"
            )]
    
    async def run(self):
        """Ejecuta el servidor MCP"""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Punto de entrada principal"""
    server = PowerBIModelServer(MODELS_PATH)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
