# Power BI Semantic Model Management Library

---

## 🦆 Integración con DuckDB (rama mcpconduckdb)

En esta rama, la base de datos DuckDB se utiliza como **fuente central de información** para el análisis y gestión de dependencias en modelos y reportes de Power BI. Casi todas las operaciones del MCP se basan en los datos almacenados en DuckDB, lo que permite:

- Parsear y guardar información de **visuales** de reportes (tipo, campos usados, posición, etc.)
- Almacenar detalles de **modelos semánticos**, incluyendo tablas, columnas, relaciones y medidas
- Registrar el uso de columnas y medidas en cada visual y reporte
- Consultar rápidamente dependencias entre reportes, tablas y columnas
- Optimizar la detección de elementos no utilizados y la generación de submodelos

**La idea principal:**

> Toda la lógica de análisis de dependencias y optimización de modelos/reportes se apoya en la información estructurada y consultable de DuckDB, en vez de recorrer archivos y carpetas cada vez.

Esto permite mayor velocidad, consultas complejas y una base sólida para futuras automatizaciones.

**Español | [English](README_EN.md)**

---

Biblioteca de Python para manipular modelos semánticos de Power BI (archivos `.SemanticModel` y `.Report`) de forma programática.

## 🚀 Características

- **Carga y guardado** de modelos semánticos completos
- **Creación de submodelos** con filtrado inteligente de tablas y relaciones
- **Filtrado de elementos** (columnas, medidas, jerarquías) con modos include/exclude
- **Análisis de reportes** (.Report) para extraer columnas y medidas usadas
- **Generación de SVG** de páginas de reportes con visuales
- **Preservación de metadatos** y propiedades originales
- **Soporte para TMDL** (formato de definición de modelos tabulares)
- **Integración con Claude Desktop** vía servidor MCP

## 📦 Instalación

```bash
# Clonar el repositorio
git clone https://github.com/megeagomez/SemanticModelGenerator.git
cd "pyconstelaciones + Reports"

# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Windows CMD:
.\.venv\Scripts\activate.bat
# Linux/Mac:
source .venv/bin/activate

# Instalar dependencias (si las hay)
# pip install -r requirements.txt
```

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
- [MCP_SERVER](MCP_SERVER.md) - Integración con Claude Desktop
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
