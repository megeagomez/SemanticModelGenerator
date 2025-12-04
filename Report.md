# Clase clsReport - Análisis de Reportes Power BI

Clases para analizar y trabajar con archivos `.Report` de Power BI, incluyendo extracción de columnas y medidas utilizadas, y generación de visualizaciones SVG.

## Diagrama de Clases

```
clsReport
├── pages: List[Page]
├── SemanticModel: str
└── filterConfig: Dict

Page (hereda FilterMixin)
├── visuals: List[Visual]
├── filters: List[str]
└── displayName: str

Visual
├── visualType: str
├── columns_used: List[str]
├── measures_used: List[str]
└── position: Dict

FilterMixin
└── extract_filter_descriptions()
```

## Clase Visual

Representa un visual individual dentro de una página del reporte.

### Propiedades

```python
visual = Visual(visual_dir)

# Propiedades básicas
visual.name              # str: Nombre del visual
visual.visualType        # str: Tipo (slicer, donutchart, card, etc.)
visual.text              # str: Texto mostrado en el visual
visual.navigationTarget  # str: Objetivo de navegación
visual.position          # Dict: {x, y, width, height}

# Referencias a datos
visual.columns_used      # List[str]: Columnas usadas, formato "Tabla.Columna"
visual.measures_used     # List[str]: Medidas usadas, formato "Tabla.Medida"
```

### Ejemplo de uso

```python
from models import Visual

visual = Visual("Modelos/FullAdventureWorks.Report/definition/pages/page1/visuals/visual1")

print(f"Tipo: {visual.visualType}")
print(f"Columnas: {visual.columns_used}")
print(f"Medidas: {visual.measures_used}")
# Tipo: donutchart
# Columnas: ['DimProduct.Color', 'DimProduct.EnglishProductName']
# Medidas: ['FactInternetSales.OrderQuantity']
```

## Clase Page

Representa una página completa del reporte con todos sus visuales.

### Propiedades

```python
page = Page(page_dir)

# Información de la página
page.name              # str: Nombre interno
page.displayName       # str: Nombre visible
page.width             # int: Ancho en píxeles
page.height            # int: Alto en píxeles

# Contenido
page.visuals           # List[Visual]: Lista de visuales
page.filters           # List[str]: Descripción de filtros
page.filterConfig      # Dict: Configuración de filtros
```

### Métodos principales

```python
# Obtener todas las columnas usadas en la página
columns = page.get_all_columns_used()
# Returns: Set[str] - {'DimProduct.Color', 'DimCustomer.MaritalStatus', ...}

# Obtener todas las medidas usadas en la página
measures = page.get_all_measures_used()
# Returns: Set[str] - {'FactInternetSales.OrderQuantity', ...}

# Generar SVG de la página
svg_content = page.generate_svg_page()
# Returns: str - Código SVG completo con todos los visuales
```

### Visuales SVG soportados

La clase `Page` puede generar representaciones SVG de los siguientes tipos de visuales:

- `slicer` - Segmentador
- `donutchart` - Gráfico de anillos
- `piechart` - Gráfico circular
- `clusteredcolumnchart` - Gráfico de columnas agrupadas
- `columnchart` - Gráfico de columnas
- `funnel` - Embudo
- `card` - Tarjeta KPI
- `kpi` - Indicador KPI
- `textbox` - Cuadro de texto
- `table` - Tabla
- `areachart` - Gráfico de áreas
- `lineClusteredColumnComboChart` - Gráfico combinado
- `ribbonchart` - Gráfico de cinta
- `bcicalendar` - Calendario personalizado

### Ejemplo de generación SVG

```python
from models import Page

page = Page("Modelos/FullAdventureWorks.Report/definition/pages/ReportSection1")

# Generar SVG
svg = page.generate_svg_page()

# Guardar como archivo
with open("page_preview.svg", "w", encoding="utf-8") as f:
    f.write(svg)
```

## Clase clsReport

Clase principal para cargar y analizar un reporte completo de Power BI.

### Constructor

```python
from models import clsReport

report = clsReport(root_path)
```

**Parámetros:**
- `root_path` (str): Ruta a la carpeta `.Report`

### Propiedades

```python
# Información del reporte
report.SemanticModel     # str: Nombre del modelo semántico asociado
report.pages             # List[Page]: Lista de páginas del reporte
report.pageOrder         # List[str]: Orden de las páginas
report.activePageName    # str: Nombre de la página activa

# Configuración
report.filterConfig      # Dict: Configuración de filtros del reporte
report.allfilters        # List[str]: Descripciones de filtros
report.settings          # Dict: Configuración del reporte
report.themeCollection   # Dict: Temas visuales
```

### Métodos principales

#### get_all_columns_used()

Retorna todas las columnas usadas en el reporte, organizadas por tabla.

```python
columns = report.get_all_columns_used()
# Returns: Dict[str, Set[str]]
# Ejemplo:
# {
#     'DimProduct': {'Color', 'EnglishProductName', 'ProductKey'},
#     'DimCustomer': {'MaritalStatus', 'CustomerKey'},
#     'FactInternetSales': {'ProductKey', 'CustomerKey'}
# }
```

#### get_all_measures_used()

Retorna todas las medidas usadas en el reporte, organizadas por tabla.

```python
measures = report.get_all_measures_used()
# Returns: Dict[str, Set[str]]
# Ejemplo:
# {
#     'FactInternetSales': {'OrderQuantity', 'SalesAmount'}
# }
```

## Ejemplos Completos

### Analizar un reporte

```python
from models import clsReport

# Cargar reporte
report = clsReport("Modelos/FullAdventureWorks.Report")

print(f"Modelo semántico: {report.SemanticModel}")
print(f"Número de páginas: {len(report.pages)}")

# Ver columnas usadas
for table, columns in report.get_all_columns_used().items():
    print(f"\n{table}:")
    for col in sorted(columns):
        print(f"  - {col}")

# Ver medidas usadas
for table, measures in report.get_all_measures_used().items():
    print(f"\n{table} (medidas):")
    for meas in sorted(measures):
        print(f"  - {meas}")
```

### Crear modelo optimizado basado en reportes

```python
from models import clsReport, SemanticModel, TableElementSpec
from pathlib import Path
from collections import defaultdict

# Analizar todos los reportes
all_columns = defaultdict(set)
all_measures = defaultdict(set)

for report_dir in Path("Modelos").glob("*.Report"):
    report = clsReport(str(report_dir))
    
    # Agregar columnas
    for table, columns in report.get_all_columns_used().items():
        all_columns[table].update(columns)
    
    # Agregar medidas
    for table, measures in report.get_all_measures_used().items():
        all_measures[table].update(measures)

# Crear especificaciones de elementos
element_specs = {}
for table in all_columns.keys():
    cols = list(all_columns[table])
    meas = list(all_measures.get(table, []))
    
    element_specs[table] = TableElementSpec(
        columns=cols,
        measures=meas,
        mode='include'
    )

# Cargar modelo completo
model = SemanticModel("Modelos/FullAdventureWorks.SemanticModel")
model.load_from_directory()

# Crear submodelo optimizado
subset = model.create_subset_model(
    table_specs=list(all_columns.keys()),
    subset_name="OptimizedForReports.SemanticModel",
    recursive=False,  # Solo tablas usadas
    table_elements=element_specs
)

print(f"Modelo creado con {len(subset.tables)} tablas")
```

### Generar SVG de todas las páginas

```python
from models import clsReport
from pathlib import Path

report = clsReport("Modelos/FullAdventureWorks.Report")

# Crear carpeta de salida
output_dir = Path("svg_output")
output_dir.mkdir(exist_ok=True)

# Generar SVG para cada página
for page in report.pages:
    svg_content = page.generate_svg_page()
    
    filename = f"{page.displayName or page.name}.svg"
    filepath = output_dir / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(svg_content)
    
    print(f"Generado: {filepath}")
```

## Clase FilterMixin

Mixin que proporciona métodos para extraer descripciones legibles de filtros.

### Método extract_filter_descriptions()

```python
filter_mixin = FilterMixin()
descriptions = filter_mixin.extract_filter_descriptions(filter_config)

# Returns: List[str]
# Ejemplo:
# [
#     "Filtro 'Year': Se incluyen solo valores 2023 en 'DimDate'.'CalendarYear'.",
#     "Filtro 'Region': Se excluyen valores 'Northwest' en 'DimGeography'.'Region'."
# ]
```

## Notas Importantes

1. **Formato de referencias**: Todas las referencias a columnas y medidas usan el formato `"Tabla.Campo"` (con punto, sin corchetes).

2. **Auto-detección del modelo**: `clsReport` extrae automáticamente el nombre del modelo semántico del archivo `definition.pbir`.

3. **Tipos de visual**: Los tipos de visual se normalizan a minúsculas para la generación SVG.

4. **Archivos requeridos**: El reporte debe tener la estructura estándar:
   ```
   *.Report/
   ├── definition.pbir
   └── definition/
       ├── report.json
       └── pages/
           ├── pages.json
           └── ReportSection1/
               ├── page.json
               └── visuals/
                   └── visualId/
                       └── visual.json
   ```

## Ver también

- [SemanticModel](SemanticModel.md) - Clase principal para modelos semánticos
- [Table](Table.md) - Clase para tablas y sus elementos
- [InmonMode.py](../InmonMode.py) - Ejemplo de uso completo
- [MCP_SERVER.md](../MCP_SERVER.md) - Integración con Claude Desktop
