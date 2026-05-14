# Power BI Semantic Model & Report Management

> Administra, analiza y optimiza tus modelos semánticos y reportes de Power BI desde VS Code, Claude Desktop o línea de comandos.

**Español | [English](README_EN.md)**

---

## 🎯 ¿Qué hace esta herramienta?

Esta herramienta te permite trabajar con tus modelos y reportes de Power BI de forma programática, sin necesidad de abrir Power BI Desktop. Ofrece tres capacidades principales:

### 1. 🔌 Servidor MCP (Model Context Protocol)
Integración directa con **GitHub Copilot** y **Claude Desktop** para interactuar con tus modelos y reportes usando lenguaje natural:
- "¿Qué tablas tiene mi modelo AdventureWorks?"
- "Muéstrame todas las columnas que usa el reporte de ventas"
- "Crea un submodelo con solo las tablas que necesita este informe"
- "Genera la documentación HTML de todos mis reportes"

### 2. 📦 Descarga de Workspaces completos desde Power BI
**Sin limitaciones de tiempo ni consumo de tokens de API**:
- Descarga workspaces completos sin timeouts (ideal para workspaces grandes)
- Procesa modelos y reportes uno por uno sin límites de llamadas API
- Almacena toda la información en DuckDB para análisis posteriores
- Evita la necesidad de descargar archivos `.pbix` manualmente

### 3. 🧰 Conjunto completo de herramientas para análisis y optimización
- **Análisis de dependencias**: Qué tablas/columnas/medidas usa cada reporte
- **Generación de submodelos**: Crea modelos optimizados con solo lo que necesitas
- **Documentación automática**: Genera documentación HTML profesional de tus reportes
- **Visualización**: Genera mockups SVG de las páginas de tus reportes
- **Consultas SQL**: Accede a toda la metadata con consultas DuckDB

---

## 🚀 Casos de uso

### 📊 Documenta automáticamente tus reportes
```
Genera la documentación completa de todos mis reportes en HTML
```
El sistema creará documentos HTML detallados con:
- Estructura de páginas y visuales
- Mockups SVG de cada página
- Tablas, columnas y métricas utilizadas
- Código DAX de las medidas
- Código M de las fuentes de datos

### 🔍 Identifica qué elementos están en uso
```
Analiza el uso del modelo "Sales" y dime qué columnas no están siendo utilizadas
```
Útil para:
- Limpiar modelos grandes
- Reducir el tamaño de los datasets
- Identificar elementos obsoletos

### ⚡ Optimiza modelos grandes
```
Crea un submodelo llamado "Sales_Light" con solo las tablas que usa el reporte "Dashboard Ejecutivo"
```
Beneficios:
- Modelos más pequeños y rápidos
- Menor consumo de memoria
- Mejor rendimiento en Power BI Service

### 🔄 Descarga workspaces sin límites
```bash
python Importer/src/import_from_powerbi.py --workspace "Producción" --dest "D:/data"
```
Ventajas:
- Sin timeouts por workspaces grandes
- Procesamiento secuencial sin límites de API
- Toda la información guardada en DuckDB local

---

## 📋 Inventario completo de herramientas MCP

### 🔐 Autenticación Power BI
| Herramienta | Descripción |
|------------|-------------|
| `powerbi_login_interactive` | Inicia sesión en Power BI (device code flow) |
| `powerbi_check_auth_status` | Verifica el estado de autenticación |
| `powerbi_logout` | Cierra sesión y borra tokens |

### 📂 Gestión de Workspaces
| Herramienta | Descripción |
|------------|-------------|
| `powerbi_list_workspaces` | Lista todos tus workspaces |
| `powerbi_list_reports` | Lista reportes de un workspace |
| `powerbi_list_semantic_models` | Lista modelos semánticos de un workspace |
| `powerbi_download_workspace` | **Descarga completa de un workspace** (sin timeouts) |

### 🗂️ Análisis de Modelos
| Herramienta | Descripción |
|------------|-------------|
| `get_model_info` | Información detallada de un modelo (tablas, relaciones, culturas) |
| `get_table_details` | Detalles de una tabla específica (columnas, medidas, particiones) |
| `analyze_model_usage` | Qué elementos del modelo se usan en reportes |
| `analyze_model_usage_bd` | Análisis avanzado usando DuckDB |

### 📄 Análisis de Reportes
| Herramienta | Descripción |
|------------|-------------|
| `analyze_report` | Extrae todas las referencias a tablas/columnas de un reporte |
| `get_report_pages` | Lista páginas de un reporte con sus visuales |
| `get_page_visuals` | Obtiene visuales de una página específica |
| `generate_report_svg` | Genera mockup SVG de una página |
| `generate_report_documentation` | **Genera documentación HTML completa** (con SVG, DAX, M, etc.) |

### 🛠️ Creación y Optimización
| Herramienta | Descripción |
|------------|-------------|
| `create_subset_model` | Crea un submodelo con tablas específicas y sus relaciones |
| `create_model_from_reports` | **Modelo optimizado con SOLO lo usado en reportes específicos** |

### 💾 Base de Datos DuckDB
| Herramienta | Descripción |
|------------|-------------|
| `default_db` | Establece la base de datos DuckDB por defecto |
| `querydb` | Ejecuta consultas SQL en DuckDB |

### ⚙️ Configuración
| Herramienta | Descripción |
|------------|-------------|
| `set_models_path` | Cambia el directorio base de modelos y reportes |

---

## 🦆 Arquitectura: DuckDB como fuente central

Esta herramienta utiliza **DuckDB** como base de datos central para almacenar y consultar toda la metadata de tus modelos y reportes:

- ✅ **Análisis rápidos**: Sin necesidad de parsear archivos cada vez
- ✅ **Consultas SQL complejas**: Usa SQL estándar para análisis avanzados
- ✅ **Sin límites de API**: Toda la información local
- ✅ **Trazabilidad completa**: Historial de cambios y versiones

**Tablas principales en DuckDB:**
- `report`: Información de reportes
- `report_page`: Páginas de cada reporte
- `report_visual`: Visuales y su configuración
- `report_column_used`: Columnas usadas por cada visual
- `report_measure_used`: Medidas usadas por cada visual
- `semantic_model`: Modelos semánticos
- `model_table`: Tablas de cada modelo
- `model_column`: Columnas de cada tabla
- `model_measure`: Medidas DAX
- `model_relationship`: Relaciones entre tablas

---

## 📝 Flujo recomendado de trabajo

### Opción A: Usando MCP con Copilot/Claude (Recomendado)

**1. Configura el servidor MCP** (ver sección de instalación abajo)

**2. Descarga un workspace desde Power BI:**
```
Descarga el workspace "Producción" a la carpeta D:/data
```

**3. Analiza y documenta:**
```
Genera la documentación completa de todos los reportes del workspace
```

**4. Optimiza modelos:**
```
Crea un submodelo del modelo "Sales" que solo incluya las tablas usadas en el reporte "Dashboard Ejecutivo"
```

**5. Consulta directamente la metadata:**
```
Muéstrame todas las medidas DAX que contienen la palabra "Profit"
```

### Opción B: Usando línea de comandos

**1. Descarga workspace desde Power BI:**
```bash
python Importer/src/import_from_powerbi.py --workspace "Producción" --dest "D:/data" --db "powerbi.duckdb"
```

**2. Genera documentación de reportes:**
```bash
python scripts/documenta_report.py --report "Dashboard Ejecutivo" --db "D:/data/powerbi.duckdb"
```

**3. Consulta la base de datos:**
```bash
python sql_query.py --query "SELECT * FROM report WHERE report_name LIKE '%Sales%'"
```

### Opción C: Usando Python directamente

```python
from Importer.src.import_from_powerbi import import_from_powerbi

# Descarga workspace
import_from_powerbi(
    workspace_name="Producción",
    db_path="D:/data/powerbi.duckdb",
    destination_path="D:/data"
)

# Consulta modelos y reportes
from models import SemanticModel, clsReport
model = SemanticModel("D:/data/Producción/Sales.SemanticModel")
model.load_from_directory(...)

report = clsReport("D:/data/Producción/Dashboard.Report")
columns_used = report.get_all_columns_used()
```

---

## ⚙️ Instalación y configuración

### Requisitos previos
- Python 3.8 o superior
- Visual Studio Code (para usar con Copilot) o Claude Desktop

### 1. Instala las dependencias

```bash
pip install -r requirements.txt
```

### 2. Configura el servidor MCP

#### Para GitHub Copilot en VS Code:

Agrega en tu `settings.json` de VS Code (`Ctrl+Shift+P` → "Preferences: Open User Settings (JSON)"):

```json
{
  "github.copilot.mcp.servers": {
    "powerbi-semantic-model": {
      "command": "python",
      "args": ["RUTA_COMPLETA/mcp_server.py"],
      "cwd": "RUTA_COMPLETA"
    }
  }
}
```

Reemplaza `RUTA_COMPLETA` con la ruta a este proyecto.

#### Para Claude Desktop:

Edita el archivo de configuración según tu sistema:

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "powerbi-semantic-model": {
      "command": "python",
      "args": ["RUTA_COMPLETA/mcp_server.py"]
    }
  }
}
```

### 3. Reinicia la aplicación (VS Code o Claude Desktop)

### 4. Prueba la conexión

En Copilot o Claude, escribe:
```
Lista los modelos semánticos disponibles
```

Si funciona, ¡ya estás listo!

---

## 💡 Ejemplos de uso con lenguaje natural

Una vez configurado el MCP, puedes usar comandos como:

### Exploración
- "Lista todos los workspaces de Power BI"
- "¿Qué reportes hay en el workspace 'Ventas'?"
- "Muéstrame la estructura del modelo 'AdventureWorks'"

### Análisis
- "¿Qué columnas usa el reporte 'Dashboard Ejecutivo'?"
- "Analiza el uso del modelo 'Sales' y dime qué no se está usando"
- "Muéstrame todas las medidas que usan la tabla 'Calendar'"

### Creación
- "Crea un submodelo llamado 'Sales_Light' con solo las tablas: Customer, Sales, Product"
- "Genera un modelo optimizado basado en el reporte 'KPIs Mensuales'"

### Documentación
- "Genera la documentación HTML del reporte 'Dashboard Ejecutivo'"
- "Crea un mockup SVG de la primera página del reporte 'Ventas'"

### Consultas avanzadas
- "Ejecuta una consulta SQL: SELECT table_name, COUNT(*) as col_count FROM model_column GROUP BY table_name"
- "¿Cuántas medidas DAX hay en total?"

---

## 🔧 Solución de problemas

### El MCP no se conecta
1. Verifica que la ruta en la configuración sea absoluta
2. Asegúrate de que `mcp_server.py` existe en esa ubicación
3. Reinicia completamente la aplicación (no solo recargar)
4. Revisa los logs en Claude Desktop o la consola de VS Code

### Errores de autenticación con Power BI
```
Cierra la sesión de Power BI y vuelve a iniciar sesión
```

### El workspace tarda mucho en descargarse
Esto es normal para workspaces grandes. La ventaja de esta herramienta es que NO tiene timeouts. Deja que termine el proceso.

---

## 📚 Documentación adicional

Para más información técnica, consulta:

- [Documentación de la API MCP](Documentation/MCP_SERVER.md)
- [Formato PBIR y Legacy](Documentation/DUAL_FORMAT_SUPPORT.md)
- [Historial de cambios](Documentation/CHANGELOG.md)
- [Guía de configuración detallada](Documentation/SETUP_MCP_COPILOT.md)

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Haz un fork del proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto está bajo licencia MIT. Ver el archivo `LICENSE` para más detalles.

---

## 👥 Autor

Miguel Egea - [@megeagomez](https://github.com/megeagomez)

---

**¿Preguntas o problemas?** Abre un [issue](https://github.com/megeagomez/SemanticModelGenerator/issues) en GitHub.

## ⚙️ Configuración del MCP Server

El servidor MCP está configurado para almacenar todos los datos, caché y bases de datos en una ubicación centralizada. Por defecto, esta ruta es `D:/mcpdata`, pero puedes cambiarla según tu sistema.

### Cambiar la ruta de datos del MCP

**Opción 1: Modificar la configuración en Python**

Cuando inicies el MCP server desde código, puedes especificar la ruta:

```python
from mcp_server import PowerBIModelServer
from pathlib import Path

# Usar ruta personalizada
server = PowerBIModelServer(
    models_path=Path("Modelos"),
    data_path="D:/mcpdata"  # Cambiar a tu ruta preferida
)
```

**Opción 2: Usar en diferentes sistemas**

- **Windows:** `D:/mcpdata` o `C:/ProgramData/mcpdata`
- **Linux/Mac:** `/opt/mcpdata` o `$HOME/.mcpdata`

### Estructura de carpetas

Una vez configurada, el MCP creará automáticamente la siguiente estructura:

```
D:/mcpdata/
├── demostracion.duckdb       # BD por defecto
├── powerbi.duckdb            # BD de importaciones
├── powerbiinfo.json          # Información de workspaces
├── powerbi_auth_status.json  # Estado de autenticación
├── fabric_token_cache.json   # Token de autenticación (creado tras login)
└── DemoADN/                  # Workspace descargado
    ├── modelo.SemanticModel/
    ├── modelo.Report/
    └── ...
```

### Cambiar ruta en tiempo de ejecución

Si necesitas cambiar la ruta de datos mientras el servidor está ejecutándose:

```python
from Importer.src.import_from_powerbi import set_data_path

# Cambiar ruta antes de hacer login
set_data_path("D:/otra_ruta")
```

## 🔧 Uso Básico

### Cargar y copiar un modelo completo

```python
from pathlib import Path
from models import SemanticModel

# Cargar modelo
source_path = Path("Modelos/FullAdventureWorks.SemanticModel")
model = SemanticModel(str(source_path))
model.load_from_directory(source_path)

# Guardar copia
target_path = Path("Modelos/CopyModel.SemanticModel")
model.save_to_directory(target_path)
```

### Crear un submodelo con tablas específicas

```python
# Crear submodelo con búsqueda recursiva
subset = model.create_subset_model(
    table_specs=[
        ("FactInternetSales", "ManyToOne"),  # Incluir dimensiones relacionadas
        ("DimProduct", "Both")               # Buscar en ambas direcciones
    ],
    subset_name="SalesModel.SemanticModel",
    recursive=True,
    max_depth=3
)

subset.save_to_directory(Path("Modelos/SalesModel.SemanticModel"))
```

### Filtrar columnas y medidas

```python
from models import TableElementSpec

# Definir qué elementos incluir/excluir
element_specs = {
    "FactInternetSales": TableElementSpec(
        columns=["SalesAmount", "OrderQuantity"],
        measures=["Total Sales"],
        mode='include'  # Solo incluir estos elementos
    ),
    "DimCustomer": TableElementSpec(
        columns=["Phone", "EmailAddress"],
        mode='exclude'  # Excluir estos elementos
    )
}

subset = model.create_subset_model(
    table_specs=["FactInternetSales", "DimCustomer"],
    subset_name="FilteredModel.SemanticModel",
    table_elements=element_specs
)
```

### Analizar reportes y crear submodelo basado en uso

```python
from models import clsReport
from collections import defaultdict

# Analizar todos los reportes
all_references = defaultdict(set)
for report_dir in Path("Modelos").glob("*.Report"):
    report = clsReport(str(report_dir))
    references = report.get_all_columns_used()
    
    for table, columns in references.items():
        all_references[table].update(columns)

# Crear submodelo con solo las tablas/columnas usadas en reportes
element_specs = {
    table: TableElementSpec(columns=list(columns), mode='include')
    for table, columns in all_references.items()
}

subset = model.create_subset_model(
    table_specs=list(all_references.keys()),
    subset_name="ReportBasedModel.SemanticModel",
    recursive=False,  # Solo las tablas explícitas
    table_elements=element_specs
)
```

## 📚 Documentación

La documentación completa se encuentra en la carpeta [`Documentation/`](Documentation/):

- [README principal](Documentation/README.md) - Esquema de clases y ejemplos
- [SemanticModel](Documentation/SemanticModel.md) - Clase principal para modelos
- [Report](Documentation/Report.md) - Análisis de reportes Power BI
- [Table](Documentation/Table.md) - Gestión de tablas
- [Relationship](Documentation/Relationship.md) - Relaciones entre tablas
- [Model](Documentation/Model.md) - Propiedades del modelo
- [Culture](Documentation/Culture.md) - Culturas/idiomas
- [Platform](Documentation/Platform.md) - Configuración de plataforma
- [Definition](Documentation/Definition.md) - Definición del modelo
- [TmdlParser](Documentation/TmdlParser.md) - Parser de formato TMDL
- [MCP_SERVER](Documentation/MCP_SERVER.md) - Integración con Claude Desktop
- [PROMPTS_HISTORY](Documentation/PROMPTS_HISTORY.md) - Historia del desarrollo

## 🎯 Casos de Uso

1. **Crear modelos derivados por área de negocio**: Extraer solo las tablas relacionadas con ventas, finanzas, etc.
2. **Optimizar modelos para reportes específicos**: Incluir solo las columnas/medidas que realmente se usan
3. **Análisis de dependencias**: Descubrir qué reportes usan qué tablas y columnas
4. **Migraciones y copias**: Duplicar modelos manteniendo estructura y metadatos
5. **Limpieza de modelos**: Eliminar columnas no utilizadas preservando relaciones

## 🔑 Conceptos Clave

### Dirección de Búsqueda vs Cardinalidad

- **Dirección de búsqueda** (`ManyToOne`, `OneToMany`, `Both`): Controla qué tablas relacionadas se incluyen en el submodelo
- **Cardinalidad de relación**: Propiedad de cada relación que se preserva intacta (no se modifica)

### Preservación de Integridad

- Las **columnas de claves foráneas** se incluyen automáticamente si participan en relaciones
- Las **particiones** se preservan siempre (son obligatorias)
- Todos los **atributos y propiedades** se mantienen intactos

## 📝 Ejemplo Completo

Ver [`InmonMode.py`](InmonMode.py) para ejemplos completos de:
- Copia de modelos completos
- Submodelos con direcciones de búsqueda
- Filtrado de elementos por tabla
- Análisis de reportes y creación de submodelo optimizado

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## ✨ Autor

Miguel Egea

## 🙏 Agradecimientos

Desarrollado con la asistencia de GitHub Copilot y Claude AI.
