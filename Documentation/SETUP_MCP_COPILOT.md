# Configurar MCP Server de Power BI en GitHub Copilot (VS Code)

## Requisitos previos

- **VS Code** con la extensión **GitHub Copilot** instalada (v1.100+ recomendado)
- **Python 3.10+** con entorno virtual configurado
- Dependencias instaladas (`pip install -r requirements.txt`)

---

## Paso 1: Crear el archivo de configuración MCP

VS Code busca la configuración MCP en el archivo `.vscode/mcp.json` de tu workspace.

Crea el archivo `.vscode/mcp.json` con el siguiente contenido:

```json
{
  "servers": {
    "powerbi-semantic-model": {
      "type": "stdio",
      "command": "d:\\Python apps\\pyconstelaciones + Reports\\.venv\\Scripts\\python.exe",
      "args": [
        "d:\\Python apps\\pyconstelaciones + Reports\\mcp_server.py"
      ]
    }
  }
}
```

> **Nota:** Las rutas deben ser absolutas y usar `\\` en Windows.

---

## Paso 2: Habilitar MCP en VS Code

1. Abre **Settings** (`Ctrl+,`)
2. Busca `chat.mcp.enabled`
3. Asegúrate de que esté **activado** (checked)

También puedes añadirlo directamente en `.vscode/settings.json`:

```json
{
  "chat.mcp.enabled": true
}
```

---

## Paso 3: Verificar que el servidor MCP se detecta

1. Abre el **panel de Copilot Chat** (`Ctrl+Alt+I`)
2. Cambia al modo **Agent** (selecciona "Agent" en el desplegable del chat, no "Ask" ni "Edit")
3. Haz clic en el icono de **herramientas** (🔧) en la barra del chat
4. Deberías ver **"powerbi-semantic-model"** listado con todas sus herramientas
5. Si aparece un punto rojo o no aparece, haz clic en **"Start"** para iniciar el servidor

---

## Paso 4: Usar las herramientas MCP en el chat

Una vez conectado, puedes hablar en lenguaje natural y Copilot usará automáticamente las herramientas MCP. Ejemplos:

```
"¿Qué modelos semánticos tengo disponibles?"
"Analiza el reporte FullAdventureWorks"
"¿Qué tablas usa el reporte reportADN1?"
"Crea un modelo optimizado llamado MiModelo basado en FullAdventureWorks.SemanticModel"
"Ejecuta esta consulta SQL: SELECT * FROM semantic_model LIMIT 5"
```

---

## Solución de problemas

### El servidor no aparece en la lista de herramientas

1. Verifica que `.vscode/mcp.json` tenga JSON válido
2. Confirma que la ruta al intérprete Python es correcta:
   ```powershell
   & "d:\Python apps\pyconstelaciones + Reports\.venv\Scripts\python.exe" --version
   ```
3. Prueba ejecutar el servidor manualmente:
   ```powershell
   & "d:\Python apps\pyconstelaciones + Reports\.venv\Scripts\python.exe" "d:\Python apps\pyconstelaciones + Reports\mcp_server.py"
   ```
   Si funciona, esperará entrada por stdin (es normal). Pulsa `Ctrl+C` para cerrarlo.
4. Recarga VS Code (`Ctrl+Shift+P` → "Developer: Reload Window")

### Error "Module not found: mcp"

```powershell
& "d:\Python apps\pyconstelaciones + Reports\.venv\Scripts\activate.ps1"
pip install -r requirements.txt
```

### El servidor se inicia pero Copilot no lo usa

- Asegúrate de estar en modo **Agent** (no "Ask" ni "Edit")
- Verifica que `chat.mcp.enabled` está activado
- Las herramientas MCP solo se invocan cuando la pregunta es relevante

### Error DuckDB "database is locked"

Cierra cualquier otro proceso que tenga abierta la base de datos DuckDB.

---

## Herramientas disponibles

Una vez conectado, tendrás acceso a estas herramientas desde el chat:

| Herramienta | Descripción |
|---|---|
| `powerbi_login_interactive` | Login interactivo a Power BI |
| `powerbi_check_auth_status` | Verificar estado de autenticación |
| `powerbi_logout` | Cerrar sesión |
| `powerbi_list_workspaces` | Listar workspaces |
| `powerbi_list_reports` | Listar reportes |
| `powerbi_list_semantic_models` | Listar modelos semánticos |
| `powerbi_download_workspace` | Descargar workspace completo |
| `get_model_info` | Estructura del modelo |
| `get_table_details` | Detalle de una tabla |
| `create_subset_model` | Crear submodelo manual |
| `create_model_from_reports` | Crear modelo optimizado desde DuckDB |
| `analyze_report` | Analizar uso de tablas/columnas en reporte |
| `get_report_pages` | Listar páginas del reporte |
| `get_page_visuals` | Visuales de una página |
| `generate_report_svg` | Generar SVG del layout |
| `analyze_model_usage` | Análisis de uso (filesystem) |
| `analyze_model_usage_bd` | Análisis de uso (DuckDB) |
| `default_db` | Seleccionar workspace/BD activa |
| `set_models_path` | Configurar ruta de modelos |
| `querydb` | Consulta SQL directa a DuckDB |

---

## Referencia rápida de archivos

| Archivo | Propósito |
|---|---|
| `mcp_server.py` | Servidor MCP (punto de entrada) |
| `.vscode/mcp.json` | Configuración MCP para VS Code |
| `requirements.txt` | Dependencias Python |
| `MCP_SERVER.md` | Documentación completa del servidor |
