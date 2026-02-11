#!/usr/bin/env python3
"""
MCP Server para gestión de modelos semánticos de Power BI
Expone herramientas para crear, analizar y optimizar modelos mediante lenguaje natural
"""

import asyncio
import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import defaultdict

from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

from models import SemanticModel, TableElementSpec, clsReport


# Configuración
MODELS_PATH = Path(__file__).parent / "Modelos"


class PowerBIModelServer:
    """Servidor MCP para gestión de modelos semánticos de Power BI"""

    async def _powerbi_login_interactive(self) -> list[TextContent]:
        """Inicia el login interactivo a Power BI y devuelve el link y el código para autenticarse."""
        try:
            from Importer.src.import_from_powerbi import start_device_flow_interactive
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
        """Lista todos los reportes de un workspace."""
        try:
            from Importer.src.import_from_powerbi import powerbi_list_reports
        except Exception as e:
            return [TextContent(type="text", text=f"Error importando módulo: {e}")]

        try:
            result = powerbi_list_reports(workspace_id)
            
            if not result["success"]:
                return [TextContent(type="text", text=result["message"])]
            
            reports = result["reports"]
            output = f"📊 Reportes en el workspace ({len(reports)}):\n\n"
            for rep in reports:
                output += f"• {rep.get('displayName', rep.get('name', 'N/A'))}\n"
                output += f"  ID: {rep['id']}\n\n"
            
            return [TextContent(type="text", text=output)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error listando reportes: {e}")]

    async def _powerbi_list_semantic_models(self, workspace_id: str) -> list[TextContent]:
        """Lista todos los modelos semánticos de un workspace."""
        try:
            from Importer.src.import_from_powerbi import powerbi_list_semantic_models
        except Exception as e:
            return [TextContent(type="text", text=f"Error importando módulo: {e}")]

        try:
            result = powerbi_list_semantic_models(workspace_id)
            
            if not result["success"]:
                return [TextContent(type="text", text=result["message"])]
            
            models = result["models"]
            output = f"📦 Modelos semánticos en el workspace ({len(models)}):\n\n"
            for model in models:
                output += f"• {model.get('displayName', model.get('name', 'N/A'))}\n"
                output += f"  ID: {model['id']}\n\n"
            
            return [TextContent(type="text", text=output)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error listando modelos: {e}")]

    async def _powerbi_download_report(self, workspace_id: str, report_id: str, output_folder: str = "data") -> list[TextContent]:
        """Descarga un reporte de Power BI."""
        try:
            from Importer.src.import_from_powerbi import powerbi_download_report
        except Exception as e:
            return [TextContent(type="text", text=f"Error importando módulo: {e}")]

        try:
            result = powerbi_download_report(workspace_id, report_id, output_folder)
            
            if result["success"]:
                return [TextContent(type="text", text=result["message"])]
            else:
                return [TextContent(type="text", text=result["message"])]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error descargando reporte: {e}")]

    async def _powerbi_download_semantic_model(self, workspace_id: str, semantic_model_id: str, output_folder: str = "data") -> list[TextContent]:
        """Descarga un modelo semántico de Power BI."""
        try:
            from Importer.src.import_from_powerbi import powerbi_download_semantic_model
        except Exception as e:
            return [TextContent(type="text", text=f"Error importando módulo: {e}")]

        try:
            result = powerbi_download_semantic_model(workspace_id, semantic_model_id, output_folder)
            
            if result["success"]:
                return [TextContent(type="text", text=result["message"])]
            else:
                return [TextContent(type="text", text=result["message"])]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error descargando modelo: {e}")]

    def __init__(self, models_path: Path):
        self.models_path = models_path
        self.server = Server("powerbi-semantic-model")
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
                    name="powerbi_download_report",
                    description="Descarga un reporte específico de Power BI al directorio local.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workspace_id": {
                                "type": "string",
                                "description": "ID del workspace de Power BI"
                            },
                            "report_id": {
                                "type": "string",
                                "description": "ID del reporte a descargar"
                            },
                            "output_folder": {
                                "type": "string",
                                "description": "Carpeta de destino (opcional, default: 'data')",
                                "default": "data"
                            }
                        },
                        "required": ["workspace_id", "report_id"]
                    }
                ),
                Tool(
                    name="powerbi_download_semantic_model",
                    description="Descarga un modelo semántico específico de Power BI al directorio local.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workspace_id": {
                                "type": "string",
                                "description": "ID del workspace de Power BI"
                            },
                            "semantic_model_id": {
                                "type": "string",
                                "description": "ID del modelo semántico a descargar"
                            },
                            "output_folder": {
                                "type": "string",
                                "description": "Carpeta de destino (opcional, default: 'data')",
                                "default": "data"
                            }
                        },
                        "required": ["workspace_id", "semantic_model_id"]
                    }
                ),
                Tool(
                                   
                    name="list_semantic_models",
                    description="Lista todos los modelos semánticos disponibles (.SemanticModel)",
                    inputSchema={
                        "type": "object",
                        "properties": {},
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
                    name="list_reports",
                    description="Lista todos los reportes disponibles (.Report)",
                    inputSchema={
                        "type": "object",
                        "properties": {},
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
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            """Ejecuta una herramienta"""
            
            if name == "set_models_path":
                return await self._set_models_path(arguments["path"])

            if name == "list_semantic_models":
                return await self._list_semantic_models()

            if name == "powerbi_login_interactive":
                return await self._powerbi_login_interactive()
            
            if name == "powerbi_check_auth_status":
                return await self._powerbi_check_auth_status()
            
            if name == "powerbi_list_workspaces":
                return await self._powerbi_list_workspaces()
            
            if name == "powerbi_list_reports":
                return await self._powerbi_list_reports(arguments["workspace_id"])
            
            if name == "powerbi_list_semantic_models":
                return await self._powerbi_list_semantic_models(arguments["workspace_id"])
            
            if name == "powerbi_download_report":
                return await self._powerbi_download_report(
                    arguments["workspace_id"],
                    arguments["report_id"],
                    arguments.get("output_folder", "data")
                )
            
            if name == "powerbi_download_semantic_model":
                return await self._powerbi_download_semantic_model(
                    arguments["workspace_id"],
                    arguments["semantic_model_id"],
                    arguments.get("output_folder", "data")
                )
            
            elif name == "get_model_info":
                return await self._get_model_info(arguments["model_name"])
            
            elif name == "list_reports":
                return await self._list_reports()
            
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
            
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _list_semantic_models(self) -> list[TextContent]:
        """Lista todos los modelos semánticos"""
        models = [d.name for d in self.models_path.iterdir() 
                 if d.is_dir() and d.name.endswith('.SemanticModel')]
        
        result = f"Modelos semánticos encontrados ({len(models)}):\n\n"
        for model in sorted(models):
            result += f"- {model}\n"
        
        return [TextContent(type="text", text=result)]

    async def _set_models_path(self, path_str: str) -> list[TextContent]:
        """Actualiza el directorio base de modelos y reportes."""
        new_path = Path(path_str)
        # Permitir relativo al cwd donde corre el servidor
        if not new_path.is_absolute():
            new_path = (Path.cwd() / new_path).resolve()
        if not new_path.exists() or not new_path.is_dir():
            return [TextContent(type="text", text=f"Error: la ruta especificada no existe o no es un directorio: {new_path}")]

        self.models_path = new_path
        return [TextContent(type="text", text=f"✅ Directorio de modelos actualizado a: {self.models_path}")]
    
    async def _get_model_info(self, model_name: str) -> list[TextContent]:
        """Obtiene información de un modelo"""
        model_path = self.models_path / model_name
        
        if not model_path.exists():
            return [TextContent(type="text", text=f"Error: Modelo '{model_name}' no encontrado")]
        
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
    
    async def _list_reports(self) -> list[TextContent]:
        """Lista todos los reportes"""
        reports = [d.name for d in self.models_path.iterdir() 
                  if d.is_dir() and d.name.endswith('.Report')]
        
        result = f"Reportes encontrados ({len(reports)}):\n\n"
        for report in sorted(reports):
            result += f"- {report}\n"
        
        return [TextContent(type="text", text=result)]
    
    async def _analyze_report(self, report_name: str) -> list[TextContent]:
        """Analiza un reporte"""
        report_path = self.models_path / report_name
        
        if not report_path.exists():
            return [TextContent(type="text", text=f"Error: Reporte '{report_name}' no encontrado")]
        
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
    
    async def _generate_report_svg(self, report_name: str, page_name: Optional[str] = None, save_to_file: bool = False) -> list[TextContent]:
        """Genera una visualización SVG de una página de reporte"""
        report_path = self.models_path / report_name
        
        if not report_path.exists():
            return [TextContent(type="text", text=f"Error: Reporte '{report_name}' no encontrado")]
        
        # Parsear reporte
        report = clsReport(str(report_path))
        
        if not report.pages:
            return [TextContent(type="text", text=f"Error: El reporte no tiene páginas")]
        
        # Buscar página
        target_page = None
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
            result += f"Página: {display_name}\n"
            result += f"Visuales renderizados: {len(target_page.visuals)}\n"
            result += f"Tamaño del SVG: {len(svg_content)} caracteres\n\n"
            result += "--- Vista previa (primeros 500 caracteres) ---\n"
            result += svg_content[:500] + "..."
        else:
            display_name = target_page.displayName if target_page.displayName else target_page.name
            result = f"=== SVG de la Página: {display_name} ===\n\n"
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
        
        # Crear submodelo
        subset = model.create_subset_model(
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
        """Crea modelo basado en reportes"""
        
        source_path = self.models_path / source_model
        if not source_path.exists():
            return [TextContent(type="text", text=f"Error: Modelo fuente '{source_model}' no encontrado")]
        
        # Si no se especifican reportes, usar todos
        if not reports:
            reports = [d.name for d in self.models_path.iterdir() 
                      if d.is_dir() and d.name.endswith('.Report')]
        
        # Analizar reportes
        all_columns = defaultdict(set)
        all_measures = defaultdict(set)
        for report_name in reports:
            report_path = self.models_path / report_name
            if not report_path.exists():
                continue
            
            report_obj = clsReport(str(report_path))
            columns_refs = report_obj.get_all_columns_used()
            measures_refs = report_obj.get_all_measures_used()
            
            for table, fields in columns_refs.items():
                all_columns[table].update(fields)
            for table, fields in measures_refs.items():
                all_measures[table].update(fields)
        
        # Cargar modelo fuente
        model = SemanticModel(str(source_path))
        model.load_from_directory(source_path)
        
        # Separar columnas y medidas por tabla
        element_specs = {}
        all_tables = set(list(all_columns.keys()) + list(all_measures.keys()))
        
        for table in all_tables:
            original_table = next((t for t in model.tables if t.name == table), None)
            if not original_table:
                continue
            
            columns_list = sorted(list(all_columns.get(table, set())))
            measures_list = sorted(list(all_measures.get(table, set())))
            
            element_specs[table] = TableElementSpec(
                columns=columns_list if columns_list else None,
                measures=measures_list if measures_list else None,
                mode='include'
            )
        
        # Crear submodelo
        subset = model.create_subset_model(
            table_specs=list(all_tables),
            subset_name=target_model,
            recursive=include_related,
            max_depth=0 if not include_related else 3,
            table_elements=element_specs
        )
        
        # Guardar
        target_path = self.models_path / target_model
        subset.save_to_directory(target_path)

        # Crear pbip + report vacío por defecto
        await self._scaffold_empty_report_and_pbip(target_model)

        # Si se solicita, copiar páginas de los reportes origen, acumulando
        if copy_reports:
            await self._copy_and_merge_report_pages(
                source_reports=reports,
                target_report_name=self._derive_report_name_from_model(target_model)
            )
        
        result = f"✅ Modelo optimizado creado: {target_model}\n\n"
        result += f"Basado en {len(reports)} reportes\n"
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
        base = model_name.replace('.SemanticModel', '')
        report_dir = self.models_path / f"{base}.Report"
        report_dir.mkdir(parents=True, exist_ok=True)

        # .platform (metadata del report)
        platform_path = report_dir / ".platform"
        platform_obj = {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
            "metadata": {
                "type": "Report",
                "displayName": base
            },
            "config": {
                "version": "2.0",
                "logicalId": str(uuid.uuid4())
            }
        }
        platform_path.write_text(json.dumps(platform_obj, indent=2), encoding="utf-8")

        # definition.pbir (link al modelo)
        pbir_path = report_dir / "definition.pbir"
        pbir_obj = {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
            "version": "4.0",
            "datasetReference": {
                "byPath": {
                    "path": f"../{model_name}"
                }
            }
        }
        pbir_path.write_text(json.dumps(pbir_obj, indent=2), encoding="utf-8")

        # Estructura básica de report
        definition_dir = report_dir / "definition"
        pages_dir = definition_dir / "pages"
        static_dir = report_dir / "StaticResources" / "SharedResources"
        definition_dir.mkdir(parents=True, exist_ok=True)
        pages_dir.mkdir(parents=True, exist_ok=True)
        static_dir.mkdir(parents=True, exist_ok=True)

        report_json = {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.0.0/schema.json",
            "themeCollection": {
                "baseTheme": {
                    "name": "CY25SU11",
                    "reportVersionAtImport": {
                        "visual": "2.4.0",
                        "report": "3.0.0",
                        "page": "2.3.0"
                    },
                    "type": "SharedResources"
                }
            },
            "resourcePackages": [
                {
                    "name": "SharedResources",
                    "type": "SharedResources",
                    "items": [
                        {
                            "name": "CY25SU11",
                            "path": "BaseThemes/CY25SU11.json",
                            "type": "BaseTheme"
                        }
                    ]
                }
            ],
            "settings": {
                "useStylableVisualContainerHeader": True,
                "exportDataMode": "AllowSummarized",
                "defaultDrillFilterOtherVisuals": True,
                "allowChangeFilterTypes": True,
                "useEnhancedTooltips": True,
                "useDefaultAggregateDisplayName": True
            }
        }
        (definition_dir / "report.json").write_text(json.dumps(report_json, indent=2), encoding="utf-8")
        
        version_json = {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
            "version": "2.0.0"
        }
        (definition_dir / "version.json").write_text(json.dumps(version_json, indent=2), encoding="utf-8")
        
        # Crear pages.json con una página vacía
        page_id = str(uuid.uuid4()).replace('-', '')[:20]  # ID de 20 caracteres
        pages_json = {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
            "pageOrder": [page_id],
            "activePageName": page_id
        }
        (pages_dir / "pages.json").write_text(json.dumps(pages_json, indent=2), encoding="utf-8")
        
        # Crear directorio de página y archivo page.json
        page_folder = pages_dir / page_id
        page_folder.mkdir(parents=True, exist_ok=True)
        
        page_json = {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json",
            "name": page_id,
            "displayName": "Página 1",
            "displayOption": "FitToPage",
            "height": 720,
            "width": 1280
        }
        (page_folder / "page.json").write_text(json.dumps(page_json, indent=2), encoding="utf-8")

        # Crear .pbip que apunte al report
        pbip_path = self.models_path / f"{base}.pbip"
        pbip_obj = {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
            "version": "1.0",
            "artifacts": [
                {"report": {"path": f"{base}.Report"}}
            ],
            "settings": {"enableAutoRecovery": True}
        }
        pbip_path.write_text(json.dumps(pbip_obj, indent=2), encoding="utf-8")

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
