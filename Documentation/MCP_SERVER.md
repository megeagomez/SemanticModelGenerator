# MCP Server para Power BI Semantic Models

Este servidor MCP (Model Context Protocol) permite interactuar con los modelos semánticos de Power BI mediante lenguaje natural. Incluye soporte completo para importar workspaces, analizar dependencias DAX transitivas, crear submodelos optimizados desde DuckDB y consultar la base de datos directamente.

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
  }
}
```

### 3. Reiniciar Claude Desktop

Después de guardar la configuración, reinicia Claude Desktop para que cargue el servidor.

---

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
- `powerbi_login_interactive` — Autentica con Power BI (device code flow)
- `powerbi_check_auth_status` — Verifica estado de login
- `powerbi_logout` — Cierra sesión y borra token
- `powerbi_list_workspaces` — Lista workspaces
- `powerbi_list_reports` — Lista reportes del workspace remoto
- `powerbi_list_semantic_models` — Lista modelos remotos
- `powerbi_download_workspace` — Descarga workspace a `data/<workspace_name>/`
  - Guarda modelos (.SemanticModel), reportes (.Report) y DuckDB
  - **Ejecuta análisis de dependencias DAX** automáticamente (ver sección DaxTokenizer)

**Fase 2: Análisis Offline** (NO requiere login)
- `default_db` — Selecciona workspace actual (cambia ruta DuckDB y directorio de modelos)
- `get_model_info` — Estructura del modelo (tablas, relaciones, culturas)
- `get_table_details` — Detalle de una tabla (columnas, medidas, particiones)
- `analyze_report` — Extrae tablas/columnas usadas por un reporte
- `get_report_pages` — Lista páginas con nombre y número de visuales
- `get_page_visuals` — Visuales de una página (tipo, posición, campos)
- `generate_report_svg` — Genera SVG visual del layout de una página
- `create_subset_model` — Crea submodelo con tablas seleccionadas manualmente (legacy)
- `create_model_from_reports` — **Crea modelo optimizado desde DuckDB** (usa dependencias DAX transitivas)
- `analyze_model_usage` — Análisis de uso por filesystem (escanea archivos .Report)
- `analyze_model_usage_bd` — Análisis de uso por DuckDB (consulta tablas de la BD)
- `querydb` — Ejecuta consultas SQL directamente contra DuckDB

**Fase 3: Configuración** (administración)
- `set_models_path` — Configurar ruta legacy (Modelos/)
- `default_db` — Establecer base DuckDB y workspace activos

### Workflow Offline-First

1. **Primera vez**: Autentica y descarga workspace
   ```
   Usuario: "Descarga el workspace demostracion"
   → powerbi_download_workspace(...)
   → Crea data/demostracion/ con modelos, reportes y demostracion.duckdb
   → Ejecuta DaxTokenizer: analiza medidas DAX y guarda dependencias transitivas
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

---

## Herramientas Disponibles

> **Nota sobre DuckDB**: El servidor utiliza DuckDB como almacén de metadatos. Al descargar un workspace se pueblan tablas con modelos, reportes, columnas, medidas, relaciones, filtros y **dependencias DAX transitivas**. Muchas herramientas consultan estas tablas para análisis más rápidos y precisos.

### 1. Autenticación y Descarga desde Power BI

| Herramienta | Descripción | Parámetros | 🗄️ DuckDB |
|---|---|---|:---:|
| `powerbi_login_interactive` | Inicia login interactivo (device code flow) | — | ❌ |
| `powerbi_check_auth_status` | Verifica estado de autenticación | — | ❌ |
| `powerbi_logout` | Cierra sesión y borra token de autenticación | — | ❌ |
| `powerbi_list_workspaces` | Lista workspaces disponibles | — | ❌ |
| `powerbi_list_reports` | Lista reportes de un workspace | `workspace_id` | ❌ |
| `powerbi_list_semantic_models` | Lista modelos semánticos de un workspace | `workspace_id` | ❌ |
| `powerbi_download_workspace` | Descarga workspace completo + análisis DAX | `workspace_name`, `destination_path`?, `db_name`? | ✅ |

### 2. Gestión de Modelos Semánticos

| Herramienta | Descripción | Parámetros | 🗄️ DuckDB |
|---|---|---|:---:|
| `get_model_info` | Estructura del modelo (tablas, relaciones, culturas) | `model_name` | ❌ |
| `get_table_details` | Detalle de una tabla (columnas, medidas, particiones) | `model_name`, `table_name` | ❌ |
| `create_subset_model` | Crea submodelo con tablas manuales (legacy) | `source_model`, `target_model`, `tables`, `search_direction`?, `recursive`?, `max_depth`? | ❌ |
| `create_model_from_reports` | **Modelo optimizado desde DuckDB** (dependencias DAX) | `source_model`, `target_model`, `reports`?, `include_related`?, `copy_reports`? | ✅ |

### 3. Análisis de Reportes

| Herramienta | Descripción | Parámetros | 🗄️ DuckDB |
|---|---|---|:---:|
| `analyze_report` | Extrae tablas/columnas/medidas del reporte | `report_name` | ❌ |
| `get_report_pages` | Lista páginas con nombre y # visuales | `report_name` | ❌ |
| `get_page_visuals` | Visuales de una página (tipo, posición, campos) | `report_name`, `page_name` | ❌ |
| `generate_report_svg` | Genera SVG del layout de la página | `report_name`, `page_name`?, `save_to_file`? | ❌ |

### 4. Análisis de Dependencias y Uso

| Herramienta | Descripción | Parámetros | 🗄️ DuckDB |
|---|---|---|:---:|
| `analyze_model_usage` | Qué tablas se usan en reportes (filesystem) | `model_name` | ❌ |
| `analyze_model_usage_bd` | Qué tablas se usan (desde DuckDB) | `model_name`, `db_path`?, `semantic_model_id`? | ✅ |

### 5. Configuración y Consultas

| Herramienta | Descripción | Parámetros | 🗄️ DuckDB |
|---|---|---|:---:|
| `default_db` | Establece base DuckDB y workspace por defecto | `db_path`, `db_name` | ⚙️ |
| `set_models_path` | Cambia directorio base legacy (Modelos/) | `path` | ❌ |
| `querydb` | Ejecuta SQL directamente contra DuckDB (read-only) | `query` | ✅ |

---

## Análisis de Dependencias DAX (DaxTokenizer)

Al descargar un workspace con `powerbi_download_workspace`, el pipeline de importación ejecuta automáticamente el **DaxTokenizer**, que:

1. **Carga todas las medidas** del modelo desde DuckDB (`semantic_model_measure`)
2. **Tokeniza las expresiones DAX** clasificando cada token (función, tabla, columna, medida, variable, operador, literal)
3. **Resuelve dependencias transitivas**: si la medida A referencia la medida B, y B referencia la tabla C, entonces A también depende de C
4. **Persiste las dependencias** en la tabla `semantic_model_measure_dependencies`

### Tabla `semantic_model_measure_dependencies`

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER | PK autoincremental |
| `semantic_model_id` | VARCHAR | GUID del modelo semántico |
| `measure_name` | VARCHAR | Nombre de la medida |
| `measure_table` | VARCHAR | Tabla que contiene la medida |
| `dependency_type` | VARCHAR | `table`, `column` o `measure` |
| `referenced_name` | VARCHAR | Nombre del objeto referenciado |
| `referenced_table` | VARCHAR | Tabla del objeto referenciado |
| `created_at` | TIMESTAMP | Fecha de creación |

> **Nota**: La tabla `semantic_model_measure_dependencies` se crea siempre al importar (aunque esté vacía), gracias a `DaxTokenizer.ensure_dependencies_table()`. Esto garantiza que `create_model_from_reports` pueda ejecutarse incluso si el análisis DAX falla.

### Ejemplo de consulta

```sql
-- Ver dependencias transitivas de una medida
SELECT dependency_type, referenced_table, referenced_name
FROM semantic_model_measure_dependencies
WHERE measure_name = 'Total Ventas'
ORDER BY dependency_type, referenced_table;
```

---

## Esquema DuckDB Completo

Al importar un workspace se crean las siguientes tablas:

| Tabla | Descripción |
|---|---|
| `semantic_model` | Modelos semánticos (id, nombre, workspace_id, semantic_model_id) |
| `semantic_model_table` | Tablas del modelo |
| `semantic_model_column` | Columnas de cada tabla |
| `semantic_model_measure` | Medidas con expresión DAX |
| `semantic_model_relationship` | Relaciones entre tablas |
| `semantic_model_measure_dependencies` | **Dependencias DAX transitivas** |
| `report` | Reportes importados |
| `report_column_used` | Columnas usadas por cada reporte |
| `report_measure_used` | Medidas usadas por cada reporte |
| `report_filter` | Filtros a nivel de reporte |
| `report_page_filter` | Filtros a nivel de página |
| `report_visual_filter` | Filtros a nivel de visual |

---

## Detalle de Herramientas Clave

### `create_model_from_reports` (optimización desde DuckDB)

Crea un modelo optimizado que contiene **solo** las tablas, columnas, medidas y relaciones necesarias para los reportes vinculados. Usa internamente `create_subset_model_from_db`.

**Proceso interno:**
1. Consulta `report_column_used` y `report_measure_used` para determinar qué elementos usan los reportes
2. Consulta `semantic_model_measure_dependencies` para resolver dependencias DAX transitivas
3. Filtra tablas y columnas del modelo fuente, manteniendo solo lo necesario
4. Reconstruye relaciones entre las tablas incluidas
5. Crea automáticamente un `.pbip` y `.Report` vacío enlazado al nuevo modelo
6. Opcionalmente copia páginas de los reportes origen al nuevo reporte (`copy_reports=true`)

**Parámetros:**
| Parámetro | Tipo | Requerido | Default | Descripción |
|---|---|:---:|---|---|
| `source_model` | string | ✅ | — | Modelo fuente (ej: `MiModelo.SemanticModel`) |
| `target_model` | string | ✅ | — | Nombre del nuevo modelo |
| `reports` | string[] | ❌ | `[]` (todos) | Reportes a analizar |
| `include_related` | boolean | ❌ | `false` | Incluir tablas relacionadas adicionales |
| `copy_reports` | boolean | ❌ | `true` | Copiar páginas de reportes origen al destino |

### `create_subset_model` (selección manual, legacy)

Crea un submodelo seleccionando tablas manualmente y siguiendo relaciones recursivamente. No usa DuckDB — trabaja directamente con los archivos TMDL.

**Parámetros:**
| Parámetro | Tipo | Requerido | Default | Descripción |
|---|---|:---:|---|---|
| `source_model` | string | ✅ | — | Modelo fuente |
| `target_model` | string | ✅ | — | Nombre del nuevo modelo |
| `tables` | string[] | ✅ | — | Tablas a incluir |
| `search_direction` | string | ❌ | `ManyToOne` | Dirección: `ManyToOne`, `OneToMany`, `Both` |
| `recursive` | boolean | ❌ | `true` | Buscar recursivamente tablas relacionadas |
| `max_depth` | integer | ❌ | `3` | Profundidad máxima de búsqueda |

### `querydb` (consultas SQL directas)

Ejecuta una consulta SQL en la base de datos DuckDB predeterminada (read-only). Útil para explorar las tablas de metadatos, verificar dependencias o hacer análisis ad-hoc.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|---|---|:---:|---|
| `query` | string | ✅ | Consulta SQL a ejecutar |

**Ejemplo:**
```sql
-- Tablas con más medidas
SELECT t.name, COUNT(m.id) as n_measures
FROM semantic_model_table t
JOIN semantic_model_measure m ON m.table_id = t.id
GROUP BY t.name ORDER BY n_measures DESC;
```

### `analyze_model_usage_bd` (análisis de uso desde DuckDB)

Analiza qué tablas/columnas/medidas de un modelo se usan en reportes, consultando las tablas `report_column_used` y `report_measure_used` de DuckDB.

**Parámetros:**
| Parámetro | Tipo | Requerido | Default | Descripción |
|---|---|:---:|---|---|
| `model_name` | string | ✅ | — | Nombre del modelo a analizar |
| `db_path` | string | ❌ | BD por defecto | Ruta a la base DuckDB |
| `semantic_model_id` | string | ❌ | Del modelo | GUID del modelo semántico |

---

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

### Crear un modelo optimizado (desde DuckDB)

```
Usuario: "Crea un modelo llamado VentasOptimizado basado en
         el modelo FullAdventureWorks.SemanticModel"

Claude: [llama a create_model_from_reports con:
  source_model="FullAdventureWorks.SemanticModel"
  target_model="VentasOptimizado.SemanticModel"
]
→ Consulta DuckDB: report_column_used + report_measure_used
→ Resuelve dependencias DAX transitivas
→ Crea modelo con solo tablas/columnas/medidas necesarias
→ Crea .pbip + .Report vacío enlazado
→ Copia páginas de reportes origen
```

### Crear submodelo con tablas específicas (legacy)

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

### Consultar DuckDB directamente

```
Usuario: "¿Cuántas dependencias DAX tiene cada medida?"
Claude: [llama a querydb con:
  query="SELECT measure_name, COUNT(*) as deps
         FROM semantic_model_measure_dependencies
         GROUP BY measure_name ORDER BY deps DESC LIMIT 20"
]
```

### Analizar qué tablas no se usan

```
Usuario: "¿Qué tablas del modelo FullAdventureWorks no se usan en ningún reporte?"
Claude: [llama a analyze_model_usage_bd con model_name="FullAdventureWorks.SemanticModel"]
```

---

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

### Error DuckDB "database is locked"

Asegúrate de que ningún otro proceso tenga abierta la base de datos. DuckDB solo permite una conexión de escritura simultánea.

---

## Arquitectura Técnica

El servidor MCP funciona como un puente entre Claude Desktop y tu biblioteca de Python:

```
Claude Desktop
    ↓ (JSON-RPC sobre stdio)
mcp_server.py (PowerBIModelServer)
    ↓ (llama a clases Python)
├── models/semantic_model.py    ← Modelos, submodelos, create_subset_model_from_db
├── models/report.py            ← Reportes (legacy + PBIR)
├── models/dax_tokenizer.py     ← Tokenización DAX + dependencias transitivas
├── Importer/src/import_from_powerbi.py  ← Pipeline de importación + DaxTokenizer
    ↓ (lee/escribe)
├── data/<workspace>/*.SemanticModel     ← Archivos TMDL
├── data/<workspace>/*.Report            ← Archivos de reporte
├── data/<workspace>/<workspace>.duckdb  ← Metadatos + dependencias DAX
└── Modelos/                             ← Directorio legacy
```

Cada herramienta del servidor es una función async que:
1. Recibe parámetros en JSON
2. Llama a las clases existentes (SemanticModel, clsReport, DaxTokenizer)
3. Devuelve resultados en formato texto (TextContent)

### Pipeline de Importación

Al ejecutar `powerbi_download_workspace`:

```
1. Autenticación con Power BI (Fabric API)
2. Descarga modelos semánticos → data/<workspace>/*.SemanticModel/
3. Descarga reportes → data/<workspace>/*.Report/
4. Guarda metadatos en DuckDB:
   - semantic_model, semantic_model_table, semantic_model_column, ...
   - report, report_column_used, report_measure_used, report_*_filter
5. DaxTokenizer.ensure_dependencies_table(conn)  ← Crea tabla vacía si no existe
6. DaxTokenizer.from_duckdb(db_path)             ← Carga medidas y tokeniza
7. tokenizer.resolve_transitive_measures()        ← Resuelve dependencias transitivas
8. tokenizer.save_dependencies_to_db(db_path)     ← Persiste en semantic_model_measure_dependencies
```

## Flujo de Trabajo Típico

1. **Importar**: `powerbi_download_workspace` descarga el workspace y analiza dependencias DAX
2. **Explorar**: `get_model_info`, `get_report_pages`, `querydb` para entender la estructura
3. **Analizar**: `analyze_model_usage_bd` para ver qué se usa y qué no
4. **Optimizar**: `create_model_from_reports` para crear modelos mínimos basados en DuckDB
5. **Verificar**: `get_model_info` para confirmar el resultado, `querydb` para consultas ad-hoc

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

# Crear submodelo (requería re-parsear reportes cada vez)
subset = model.create_subset_model(...)
subset.save_to_directory(...)
```

### Ahora (Lenguaje natural en Claude):
```
"Crea un modelo optimizado llamado VentasOptimizado basado en
FullAdventureWorks.SemanticModel"
```

Claude automáticamente:
1. Llama a `create_model_from_reports`
2. Consulta DuckDB (columnas, medidas, dependencias DAX transitivas)
3. Filtra tablas/columnas/medidas/relaciones necesarias
4. Crea el modelo + `.pbip` + `.Report`
5. Copia las páginas de los reportes origen
6. Te muestra el resumen
