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

### 1. Información y Listado

| Herramienta | Descripción | Parámetros |
|------------|-------------|------------|
| `list_semantic_models` | Lista todos los modelos .SemanticModel | - |
| `get_model_info` | Obtiene estructura del modelo | `model_name` |
| `list_reports` | Lista todos los reportes .Report | - |
| `get_table_details` | Detalles de una tabla | `model_name`, `table_name` |

### 2. Análisis de Reportes

| Herramienta | Descripción | Parámetros |
|------------|-------------|------------|
| `analyze_report` | Extrae tablas/columnas del reporte | `report_name` |
| `get_report_pages` | Lista páginas con nombre y # visuales | `report_name` |
| `get_page_visuals` | Visuales de una página (tipo, posición, campos) | `report_name`, `page_name` |
| `generate_report_svg` | Genera SVG de página de reporte | `report_name`, `page_name` (opcional), `save_to_file` (opcional) |
| `analyze_model_usage` | Qué tablas se usan en reportes | `model_name` |

### 3. Creación de Modelos

| Herramienta | Descripción | Parámetros |
|------------|-------------|------------|
| `create_subset_model` | Crea submodelo con tablas específicas | `source_model`, `target_model`, `tables`, `search_direction`, `recursive`, `max_depth` |
| `create_model_from_reports` | Modelo optimizado desde reportes | `source_model`, `target_model`, `reports`, `include_related` |

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
