# MCP Server para Power BI Semantic Models

Este servidor MCP (Model Context Protocol) permite interactuar con los modelos semánticos de Power BI mediante lenguaje natural.

## Instalación y Configuración

### 1. Instalar dependencias

```bash
# Activar entorno virtual
.venv\Scripts\activate

# Instalar MCP
pip install -r requirements.txt
```

### 2. Configurar Claude Desktop

Edita el archivo de configuración:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

Añade:

```json
{
  "mcpServers": {
    "powerbi-semantic-model": {
      "command": "D:\\Python apps\\pyconstelaciones + Reports\\.venv\\Scripts\\python.exe",
      "args": ["D:\\Python apps\\pyconstelaciones + Reports\\mcp_server.py"]
    }
  ### 3. Reiniciar Claude Desktop

  Después de guardar la configuración, reinicia Claude Desktop para que cargue el servidor.

  }
}
```

## Herramientas Disponibles

> **Nota sobre DuckDB**: Algunas herramientas utilizan una base de datos DuckDB para análisis rápido de dependencias entre modelos, reportes y elementos. Esto permite consultas más eficientes que el análisis de archivos directo.

## Arquitectura Workspace: Offline-First

El servidor utiliza una arquitectura **workspace-scoped** que separa las operaciones remotas (dependientes de API) de las locales (offline):

### Estructura de Directorios

```
MCP_ROOT/
  ├── data/
  │   ├── demostracion/              ← Workspace descargado
  │   │   ├── FullAdventureWorks.SemanticModel/
  │   │   │   ├── definition/...
  │   │   │   └── model.bim
  │   │   ├── FullAdventureWorks.Report/
  │   │   │   ├── definition.pbir
  │   │   │   └── definition/...
  │   │   ├── demostracion.duckdb    ← Metadatos del workspace
  │   │
  │   └── other_workspace/           ← Otro workspace
  │       ├── SomeModel.SemanticModel/
  │       └── other_workspace.duckdb
  │
  └── Modelos/                       ← Directorio legacy (para compatibilidad)
      ├── FullAdventureWorks.pbip
      └── ...
```

### Operaciones por Fase

**Fase 1: Autenticación Remota** (requiere login Power BI)
- `powerbi_login_interactive` - Autentica con Power BI
- `powerbi_check_auth_status` - Verifica estado de login
- `powerbi_list_workspaces` - Lista workspaces
- `powerbi_list_reports` - Lista reportes del workspace remoto
- `powerbi_list_semantic_models` - Lista modelos remotos
- `powerbi_download_workspace` - Descarga workspace a `data/<workspace_name>/`

**Fase 2: Análisis Offline** (NO requiere login)
- `default_db` - Selecciona workspace actual
- `list_semantic_models` - Lee desde `data/<workspace_name>/*.SemanticModel`
- `list_reports` - Lee desde `data/<workspace_name>/*.Report`
- `get_model_info` - Analiza modelo del workspace actual
- `analyze_report` - Analiza reporte del workspace actual
- `create_subset_model` - Crea submodelos desde datos locales
- `create_model_from_reports` - Optimiza modelo basándose en reportes locales

**Fase 3: Configuración** (administración)
- `set_models_path` - Configurar ruta legacy (Modelos/)
- `analyze_model_usage_bd` - Consulta dependencias desde DuckDB

### Workflow Offline-First

1. **Primera vez**: Autentica y descarga workspace
   ```
   Usuario: "Descarga el workspace demostracion"
   → powerbi_download_workspace(...) 
   → Crea data/demostracion/ con modelos, reportes y demostracion.duckdb
   ```

2. **Trabajo offline**: Usa herramientas locales sin login
   ```
   Usuario: "¿Qué modelos tengo?"
   → list_semantic_models (usa data/demostracion/)
   → NO requiere autenticación
   ```

3. **Cambiar workspace**: Selecciona otro workspace descargado
   ```
   Usuario: "Usa el workspace other_workspace"
   → default_db(db_path="data/other_workspace/other_workspace.duckdb", 
                 db_name="other_workspace")
   → Siguiente list_* leerá desde data/other_workspace/
   ```

### 1. Autenticación y Descarga desde Power BI

| Herramienta | Descripción | Parámetros | 🗄️ DuckDB |
|------------|-------------|------------|:----------:|
| `powerbi_login_interactive` | Inicia login interactivo (device code flow) | - | ❌ |
| `powerbi_check_auth_status` | Verifica estado de autenticación | - | ❌ |
| `powerbi_list_workspaces` | Lista workspaces disponibles | - | ❌ |
| `powerbi_list_reports` | Lista reportes de un workspace | `workspace_id` | ❌ |
| `powerbi_list_semantic_models` | Lista modelos semánticos de un workspace | `workspace_id` | ❌ |
| `powerbi_download_workspace` | Descarga workspace completo | `workspace_name`, `destination_path`, `db_name` | ✅ |

### 2. Gestión de Modelos Semánticos

| Herramienta | Descripción | Parámetros | 🗄️ DuckDB |
|------------|-------------|------------|:----------:|
| `default_db` | Selecciona workspace actual (por defecto: demostracion) | `db_path`, `db_name` | ⚙️ |
| `set_models_path` | Cambia directorio base legacy (Modelos/) | `path` | ❌ |
| `list_semantic_models` | Lista modelos de workspace actual (data/<workspace_name>/) | - | ❌ |
| `get_model_info` | Obtiene estructura del modelo | `model_name` | ❌ |
| `get_table_details` | Detalles de una tabla (columnas, medidas, particiones) | `model_name`, `table_name` | ❌ |
| `create_subset_model` | Crea submodelo con tablas específicas | `source_model`, `target_model`, `tables`, `search_direction`, `recursive`, `max_depth` | ❌ |
| `create_model_from_reports` | Modelo optimizado desde reportes | `source_model`, `target_model`, `reports`, `include_related` | ❌ |

### 3. Análisis de Reportes

| Herramienta | Descripción | Parámetros | 🗄️ DuckDB |
|------------|-------------|------------|:----------:|
| `list_reports` | Lista reportes de workspace actual (data/<workspace_name>/) | - | ❌ |
| `analyze_report` | Extrae tablas/columnas del reporte | `report_name` | ❌ |
| `get_report_pages` | Lista páginas con nombre y # visuales | `report_name` | ❌ |
| `get_page_visuals` | Visuales de una página (tipo, posición, campos) | `report_name`, `page_name` | ❌ |
| `generate_report_svg` | Genera SVG de página de reporte | `report_name`, `page_name` (opcional), `save_to_file` (opcional) | ❌ |

### 4. Análisis de Dependencias

| Herramienta | Descripción | Parámetros | 🗄️ DuckDB |
|------------|-------------|------------|:----------:|
| `analyze_model_usage` | Qué tablas se usan en reportes (filesystem) | `model_name` | ❌ |
| `analyze_model_usage_bd` | Qué tablas se usan (desde DuckDB del workspace) | `model_name`, `db_path`, `semantic_model_id` | ✅ |

### 5. Configuración

| Herramienta | Descripción | Parámetros | 🗄️ DuckDB |
|------------|-------------|------------|:----------:|
| `default_db` | Establece base DuckDB por defecto (workspace actual) | `db_path`, `db_name` | ⚙️ |

## Ejemplos de Uso en Claude

### Listar modelos disponibles

```
Usuario: "¿Qué modelos semánticos tengo?"
Claude: [llama a list_semantic_models]
```

### Analizar un reporte

```
Usuario: "¿Qué tablas y columnas usa el reporte FullAdventureWorks?"
Claude: [llama a analyze_report con report_name="FullAdventureWorks.Report"]
```

### Visualización de reportes

```
Usuario: "Dime las páginas que tiene el reporte FullAdventureWorks"
Claude: [llama a get_report_pages con report_name="FullAdventureWorks.Report"]

Usuario: "¿Qué visuales tiene la primera página del reporte?"
Claude: [primero llama a get_report_pages para obtener el nombre de la primera página,
         luego llama a get_page_visuals con ese nombre]

Usuario: "Dibujame un SVG de la página 'Overview' del reporte FullAdventureWorks"
Claude: [llama a generate_report_svg con report_name="FullAdventureWorks.Report", 
         page_name="Overview", save_to_file=False]
```

### Crear un modelo optimizado

```
Usuario: "Crea un modelo llamado VentasOptimizado que incluya solo 
         las tablas usadas en el reporte FullAdventureWorks, basándote 
         en el modelo FullAdventureWorks.SemanticModel"
         
Claude: [llama a create_model_from_reports con:
  source_model="FullAdventureWorks.SemanticModel"
  target_model="VentasOptimizado.SemanticModel"
  reports=["FullAdventureWorks.Report"]
  include_related=False
]
```

### Crear submodelo con tablas específicas

```
Usuario: "Crea un modelo SimpleVentas con las tablas FactInternetSales, 
         DimCustomer y DimProduct del modelo FullAdventureWorks, 
         buscando relaciones en ambas direcciones"
         
Claude: [llama a create_subset_model con:
  source_model="FullAdventureWorks.SemanticModel"
  target_model="SimpleVentas.SemanticModel"
  tables=["FactInternetSales", "DimCustomer", "DimProduct"]
  search_direction="Both"
  recursive=True
  max_depth=3
]
```

### Analizar qué tablas no se usan

```
Usuario: "¿Qué tablas del modelo FullAdventureWorks no se usan en ningún reporte?"
Claude: [llama a analyze_model_usage con model_name="FullAdventureWorks.SemanticModel"]
```

## Verificación del Servidor

Para probar que el servidor funciona correctamente:

```bash
# Ejecutar manualmente
.venv\Scripts\python.exe mcp_server.py
```

Si funciona, verás que espera entrada estándar (stdin). Esto es normal para servidores MCP.
Presiona Ctrl+C para detenerlo.

## Solución de Problemas

### El servidor no aparece en Claude Desktop

1. Verifica que el archivo `claude_desktop_config.json` esté bien formateado (JSON válido)
2. Asegúrate de que las rutas sean absolutas y correctas
3. Reinicia Claude Desktop completamente
4. Revisa los logs de Claude Desktop:
   - Windows: `%APPDATA%\Claude\logs`
   - macOS: `~/Library/Logs/Claude`

### Error "Module not found: mcp"

```bash
# Reinstalar dependencias
.venv\Scripts\activate
pip install -r requirements.txt
```

### Error al importar modelos

Verifica que el archivo `models/__init__.py` exporte correctamente:

```python
from .semantic_model import SemanticModel
from .table import TableElementSpec
from .report import clsReport, Visual, Page
```

## Arquitectura Técnica

El servidor MCP funciona como un puente entre Claude Desktop y tu biblioteca de Python:

```
Claude Desktop
    ↓ (JSON-RPC sobre stdio)
mcp_server.py
    ↓ (llama a clases Python)
models/semantic_model.py
models/report.py
    ↓ (lee/escribe archivos)
Modelos/*.SemanticModel
Modelos/*.Report
```

Cada herramienta del servidor es una función async que:
1. Recibe parámetros en JSON
2. Llama a las clases existentes (SemanticModel, clsReport)
3. Devuelve resultados en formato texto (TextContent)

## Flujo de Trabajo Típico

1. **Exploración**: Usar `list_semantic_models` y `list_reports` para ver qué hay disponible
2. **Análisis**: Usar `analyze_report` para ver qué tablas/columnas necesita un reporte
3. **Optimización**: Usar `create_model_from_reports` para crear modelos mínimos
4. **Verificación**: Usar `get_model_info` para confirmar el resultado

## Diferencias con uso directo de Python

### Antes (Python directo):
```python
from models import SemanticModel, clsReport

# Analizar reporte
report = clsReport("Modelos/FullAdventureWorks.Report")
refs = report.get_all_columns_used()

# Cargar modelo
model = SemanticModel("...")
model.load_from_directory(...)

# Crear submodelo
subset = model.create_subset_model(...)
subset.save_to_directory(...)
```

### Ahora (Lenguaje natural en Claude):
```
"Analiza el reporte FullAdventureWorks y crea un modelo optimizado 
llamado VentasOptimizado que incluya solo lo que necesita"
```

Claude automáticamente:
1. Llama a `analyze_report`
2. Extrae las referencias
3. Llama a `create_model_from_reports`
4. Te muestra el resumen
