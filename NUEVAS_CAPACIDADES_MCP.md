# Nuevas Capacidades MCP - Visualización de Reportes

## Resumen

Se han agregado **3 nuevas herramientas** al servidor MCP para análisis y visualización de reportes Power BI:

### 1. `get_report_pages`
**Descripción**: Lista todas las páginas de un reporte con información básica.

**Parámetros**:
- `report_name` (string): Nombre del reporte (ej: "FullAdventureWorks.Report")

**Retorna**:
- Lista de páginas con:
  - Número de página
  - Display name (nombre visible)
  - Nombre interno
  - Cantidad de visuales
  - Dimensiones (width x height)

**Ejemplo de uso en Claude**:
```
Usuario: "Dime las páginas que tiene el reporte FullAdventureWorks"
Claude: [llama a get_report_pages con report_name="FullAdventureWorks.Report"]
```

**Salida**:
```
=== Páginas del Reporte: FullAdventureWorks.Report ===

Total de páginas: 1

1. **Página 1**
   - Nombre: 31b28d69187810519133
   - Visuales: 3
   - Dimensiones: 1280x720
```

---

### 2. `get_page_visuals`
**Descripción**: Obtiene información detallada de todos los visuales de una página específica.

**Parámetros**:
- `report_name` (string): Nombre del reporte
- `page_name` (string): Nombre o displayName de la página

**Retorna**:
- Lista de visuales con:
  - Nombre del visual
  - Tipo de visual (tableEx, pivotTable, clusteredColumnChart, etc.)
  - Posición (x, y)
  - Tamaño (width, height)
  - Columnas usadas (agrupadas por tabla)
  - Medidas usadas (agrupadas por tabla)

**Ejemplo de uso en Claude**:
```
Usuario: "¿Qué visuales tiene la primera página del reporte FullAdventureWorks?"
Claude: [primero llama a get_report_pages para obtener el nombre de la primera página,
         luego llama a get_page_visuals con ese nombre]
```

**Salida**:
```
=== Visuales de la Página: Página 1 ===

Total de visuales: 3

1. **0e5597bf1895ca820271**
   - Tipo: tableEx
   - Posición: x=510.63, y=40.85
   - Tamaño: 498.97x346.26
   - Columnas (2):
     • DimCustomer.MaritalStatus
     • FactInternetSales.SalesAmount
   - Medidas (1):
     • FactInternetSales.mi media

2. **72e250773208308a0cee**
   - Tipo: pivotTable
   - Posición: x=139.97, y=34.31
   - Tamaño: 499.49x345.80
   - Columnas (2):
     • DimDate.CalendarYear
     • FactInternetSales.OrderQuantity
   - Medidas (1):
     • FactInternetSales.OrderQty
```

---

### 3. `generate_report_svg`
**Descripción**: Genera una visualización SVG de una página de reporte mostrando la disposición de todos los visuales.

**Parámetros**:
- `report_name` (string): Nombre del reporte
- `page_name` (string, opcional): Nombre o displayName de la página. Si no se especifica, usa la primera página.
- `save_to_file` (boolean, opcional): Si es `true`, guarda el SVG en un archivo además de devolverlo. Default: `false`

**Retorna**:
- Código SVG completo de la página
- Si `save_to_file=true`, también guarda en archivo `{report_name}_{page_name}.svg`

**Tipos de visuales soportados**:
- `slicer` - Segmentador
- `donutchart` - Gráfico de anillos
- `piechart` - Gráfico circular
- `clusteredcolumnchart` - Gráfico de columnas agrupadas
- `columnchart` - Gráfico de columnas
- `funnel` - Embudo
- `textbox` - Cuadro de texto
- `ribbonchart` - Gráfico de cintas
- `card` - Tarjeta
- `areachart` - Gráfico de áreas
- `table` / `tableEx` / `pivotTable` - Tablas
- `kpi` - Indicador KPI
- `lineClusteredColumnComboChart` - Gráfico combinado
- `bciCalendar` - Calendario
- Otros tipos se dibujan como rectángulo genérico

**Ejemplo de uso en Claude**:
```
Usuario: "Dibújame un gráfico SVG de la página Overview del reporte FullAdventureWorks"
Claude: [llama a generate_report_svg con 
         report_name="FullAdventureWorks.Report", 
         page_name="Overview", 
         save_to_file=False]

Usuario: "Guarda ese SVG en un archivo"
Claude: [llama a generate_report_svg con save_to_file=True]
```

**Salida (save_to_file=false)**:
```
=== SVG de la Página: Página 1 ===

Visuales renderizados: 3
Tamaño: 2814 caracteres

<svg width='1280' height='720' xmlns='http://www.w3.org/2000/svg'>
<rect width='1280' height='720' fill='#f9f9f9' stroke='#ccc'/>
<text x='10' y='20' font-family='Segoe UI' font-size='16' fill='#333'>Página: Página 1</text>
...
</svg>
```

**Salida (save_to_file=true)**:
```
✅ SVG generado y guardado en:
D:\Python apps\pyconstelaciones + Reports\Modelos\FullAdventureWorks_31b28d69187810519133.svg

Página: Página 1
Visuales renderizados: 3
Tamaño del SVG: 2814 caracteres

--- Vista previa (primeros 500 caracteres) ---
<svg width='1280' height='720' xmlns='http://www.w3.org/2000/svg'>
...
```

---

## Integración con el Código Existente

### Backend (models/report.py)
Las nuevas herramientas MCP utilizan métodos existentes de las clases:

**Clase `Page`**:
- `displayName`: Nombre visible de la página
- `name`: Nombre interno
- `width`, `height`: Dimensiones
- `visuals`: Lista de objetos Visual
- `generate_svg_page()`: Genera SVG de la página

**Clase `Visual`**:
- `name`: Identificador del visual
- `visualType`: Tipo (tableEx, clusteredColumnChart, etc.)
- `position`: Dict con x, y, width, height
- `columns_used`: Lista de referencias "Tabla.Columna"
- `measures_used`: Lista de referencias "Tabla.Medida"

**Clase `clsReport`**:
- `pages`: Lista de objetos Page
- Constructor acepta ruta al directorio .Report

### Implementación MCP (mcp_server.py)

Cada herramienta tiene:
1. **Definición en `list_tools()`**: Schema JSON con parámetros
2. **Handler en `call_tool()`**: Elif branch que llama al método correspondiente
3. **Método async `_nombre_tool()`**: Lógica que usa las clases del backend

---

## Testing

Se ha creado `test_new_tools.py` para verificar las herramientas:

```bash
python test_new_tools.py
```

**Resultados del test**:
- ✅ `get_report_pages`: Lista 1 página con 3 visuales
- ✅ `get_page_visuals`: Muestra 3 visuales (tableEx, pivotTable, clusteredColumnChart)
- ✅ `generate_report_svg`: Genera 2814 caracteres de SVG válido

---

## Casos de Uso

### 1. Exploración de Reportes
```
Usuario: "¿Qué reportes tengo disponibles?"
→ list_reports

Usuario: "¿Cuántas páginas tiene el reporte FullAdventureWorks?"
→ get_report_pages

Usuario: "¿Qué tipo de visuales hay en la página Overview?"
→ get_page_visuals
```

### 2. Análisis de Dependencias
```
Usuario: "¿Qué medidas usa el visual de ventas en la página Overview?"
→ get_page_visuals (filtra por nombre o tipo de visual)
```

### 3. Documentación Visual
```
Usuario: "Genera un diagrama de la disposición de visuales del reporte"
→ generate_report_svg (con save_to_file=true)
```

### 4. Auditoría de Reportes
```
Usuario: "Dame un resumen completo del reporte FullAdventureWorks"
→ Combina analyze_report + get_report_pages + get_page_visuals + generate_report_svg
```

---

## Próximos Pasos Sugeridos

1. **Mejoras en SVG**:
   - Agregar tooltips con información de columnas/medidas al hacer hover
   - Generar leyenda con tipos de visuales
   - Usar colores diferentes por tipo de visual

2. **Herramientas Adicionales**:
   - `get_visual_details`: Información detallada de un visual específico
   - `compare_pages`: Comparar dos páginas (visuales, campos usados)
   - `find_visual_by_field`: Buscar visuales que usan una columna/medida específica

3. **Exportación**:
   - Exportar a HTML interactivo (con zoom/pan)
   - Exportar a PNG (requeriría librería adicional como cairosvg)
   - Generar informe Markdown con todos los SVGs

4. **Integración**:
   - Agregar a la documentación oficial (README.md)
   - Crear ejemplos de uso en Jupyter Notebook
   - Video demo mostrando las capacidades

---

## Archivos Modificados

1. **mcp_server.py**:
   - Añadidos 3 tool definitions en `list_tools()`
   - Añadidos 3 elif handlers en `call_tool()`
   - Añadidos 3 métodos async: `_get_report_pages`, `_get_page_visuals`, `_generate_report_svg`

2. **MCP_SERVER.md**:
   - Actualizada tabla de herramientas
   - Agregados ejemplos de uso

3. **test_new_tools.py** (nuevo):
   - Script de prueba para las 3 nuevas herramientas

---

## Conclusión

El servidor MCP ahora puede:
- ✅ **Listar páginas** de un reporte
- ✅ **Detallar visuales** de cada página (tipo, posición, campos)
- ✅ **Generar SVG** de la disposición de visuales

Todo esto usando **lenguaje natural** a través de Claude Desktop, sin necesidad de escribir código Python manualmente.
