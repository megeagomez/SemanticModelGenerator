# Power BI Semantic Model & Report Management

> Manage, analyze, and optimize your Power BI semantic models and reports from VS Code, Claude Desktop, or command line.

**[Español](README.md) | English**

---

## 🎯 What does this tool do?

This tool allows you to work with your Power BI models and reports programmatically, without opening Power BI Desktop. It offers three main capabilities:

### 1. 🔌 MCP Server (Model Context Protocol)
Direct integration with **GitHub Copilot** and **Claude Desktop** to interact with your models and reports using natural language:
- "What tables does my AdventureWorks model have?"
- "Show me all columns used by the sales report"
- "Create a subset model with only the tables needed by this report"
- "Generate HTML documentation for all my reports"

### 2. 📦 Complete Workspace Download from Power BI
**No time limits or API token consumption**:
- Download complete workspaces without timeouts (ideal for large workspaces)
- Process models and reports one by one without API call limits
- Store all information in DuckDB for later analysis
- Avoid the need to manually download `.pbix` files

### 3. 🧰 Complete toolkit for analysis and optimization
- **Dependency analysis**: What tables/columns/measures each report uses
- **Subset model generation**: Create optimized models with only what you need
- **Automatic documentation**: Generate professional HTML documentation of your reports
- **Visualization**: Generate SVG mockups of your report pages
- **SQL queries**: Access all metadata with DuckDB queries

---

## 🚀 Use cases

### 📊 Automatically document your reports
```
Generate complete HTML documentation for all my reports
```
The system will create detailed HTML documents with:
- Page and visual structure
- SVG mockups of each page
- Tables, columns, and metrics used
- DAX code for measures
- M code for data sources

### 🔍 Identify which elements are in use
```
Analyze usage of the "Sales" model and tell me which columns are not being used
```
Useful for:
- Cleaning large models
- Reducing dataset size
- Identifying obsolete elements

### ⚡ Optimize large models
```
Create a subset model called "Sales_Light" with only the tables used by the "Executive Dashboard" report
```
Benefits:
- Smaller and faster models
- Lower memory consumption
- Better performance in Power BI Service

### 🔄 Download workspaces without limits
```bash
python Importer/src/import_from_powerbi.py --workspace "Production" --dest "D:/data"
```
Advantages:
- No timeouts for large workspaces
- Sequential processing without API limits
- All information saved in local DuckDB

---

## 📋 Complete MCP tools inventory

### 🔐 Power BI Authentication
| Tool | Description |
|------|-------------|
| `powerbi_login_interactive` | Login to Power BI (device code flow) |
| `powerbi_check_auth_status` | Verify authentication status |
| `powerbi_logout` | Logout and clear tokens |

### 📂 Workspace Management
| Tool | Description |
|------|-------------|
| `powerbi_list_workspaces` | List all your workspaces |
| `powerbi_list_reports` | List reports from a workspace |
| `powerbi_list_semantic_models` | List semantic models from a workspace |
| `powerbi_download_workspace` | **Complete workspace download** (no timeouts) |

### 🗂️ Model Analysis
| Tool | Description |
|------|-------------|
| `get_model_info` | Detailed model information (tables, relationships, cultures) |
| `get_table_details` | Specific table details (columns, measures, partitions) |
| `analyze_model_usage` | Which model elements are used in reports |
| `analyze_model_usage_bd` | Advanced analysis using DuckDB |

### 📄 Report Analysis
| Tool | Description |
|------|-------------|
| `analyze_report` | Extract all table/column references from a report |
| `get_report_pages` | List report pages with their visuals |
| `get_page_visuals` | Get visuals from a specific page |
| `generate_report_svg` | Generate SVG mockup of a page |
| `generate_report_documentation` | **Generate complete HTML documentation** (with SVG, DAX, M, etc.) |

### 🛠️ Creation and Optimization
| Tool | Description |
|------|-------------|
| `create_subset_model` | Create a subset model with specific tables and relationships |
| `create_model_from_reports` | **Optimized model with ONLY what's used in specific reports** |

### 💾 DuckDB Database
| Tool | Description |
|------|-------------|
| `default_db` | Set the default DuckDB database |
| `querydb` | Execute SQL queries in DuckDB |

### ⚙️ Configuration
| Tool | Description |
|------|-------------|
| `set_models_path` | Change the base directory for models and reports |

---

## 🦆 Architecture: DuckDB as central source

This tool uses **DuckDB** as a central database to store and query all metadata from your models and reports:

- ✅ **Fast analysis**: No need to parse files every time
- ✅ **Complex SQL queries**: Use standard SQL for advanced analysis
- ✅ **No API limits**: All information is local
- ✅ **Complete traceability**: Change history and versions

**Main tables in DuckDB:**
- `report`: Report information
- `report_page`: Pages of each report
- `report_visual`: Visuals and their configuration
- `report_column_used`: Columns used by each visual
- `report_measure_used`: Measures used by each visual
- `semantic_model`: Semantic models
- `model_table`: Tables of each model
- `model_column`: Columns of each table
- `model_measure`: DAX measures
- `model_relationship`: Relationships between tables

---

## 📝 Recommended workflow

### Option A: Using MCP with Copilot/Claude (Recommended)

**1. Configure the MCP server** (see installation section below)

**2. Download a workspace from Power BI:**
```
Download the "Production" workspace to D:/data folder
```

**3. Analyze and document:**
```
Generate complete documentation for all workspace reports
```

**4. Optimize models:**
```
Create a subset model from the "Sales" model that only includes tables used in the "Executive Dashboard" report
```

**5. Query metadata directly:**
```
Show me all DAX measures containing the word "Profit"
```

### Option B: Using command line

**1. Download workspace from Power BI:**
```bash
python Importer/src/import_from_powerbi.py --workspace "Production" --dest "D:/data" --db "powerbi.duckdb"
```

**2. Generate report documentation:**
```bash
python scripts/documenta_report.py --report "Executive Dashboard" --db "D:/data/powerbi.duckdb"
```

**3. Query the database:**
```bash
python sql_query.py --query "SELECT * FROM report WHERE report_name LIKE '%Sales%'"
```

### Option C: Using Python directly

```python
from Importer.src.import_from_powerbi import import_from_powerbi

# Download workspace
import_from_powerbi(
    workspace_name="Production",
    db_path="D:/data/powerbi.duckdb",
    destination_path="D:/data"
)

# Query models and reports
from models import SemanticModel, clsReport
model = SemanticModel("D:/data/Production/Sales.SemanticModel")
model.load_from_directory(...)

report = clsReport("D:/data/Production/Dashboard.Report")
columns_used = report.get_all_columns_used()
```

---

## ⚙️ Installation and configuration

### Prerequisites
- Python 3.8 or higher
- Visual Studio Code (to use with Copilot) or Claude Desktop

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure the MCP server

#### For GitHub Copilot in VS Code:

Add to your VS Code `settings.json` (`Ctrl+Shift+P` → "Preferences: Open User Settings (JSON)"):

```json
{
  "github.copilot.mcp.servers": {
    "powerbi-semantic-model": {
      "command": "python",
      "args": ["FULL_PATH/mcp_server.py"],
      "cwd": "FULL_PATH"
    }
  }
}
```

Replace `FULL_PATH` with the path to this project.

#### For Claude Desktop:

Edit the configuration file according to your system:

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "powerbi-semantic-model": {
      "command": "python",
      "args": ["FULL_PATH/mcp_server.py"]
    }
  }
}
```

### 3. Restart the application (VS Code or Claude Desktop)

### 4. Test the connection

In Copilot or Claude, type:
```
List available semantic models
```

If it works, you're ready!

---

## 💡 Natural language usage examples

Once the MCP is configured, you can use commands like:

### Exploration
- "List all Power BI workspaces"
- "What reports are in the 'Sales' workspace?"
- "Show me the structure of the 'AdventureWorks' model"

### Analysis
- "What columns does the 'Executive Dashboard' report use?"
- "Analyze usage of the 'Sales' model and tell me what's not being used"
- "Show me all measures using the 'Calendar' table"

### Creation
- "Create a subset model called 'Sales_Light' with only these tables: Customer, Sales, Product"
- "Generate an optimized model based on the 'Monthly KPIs' report"

### Documentation
- "Generate HTML documentation for the 'Executive Dashboard' report"
- "Create an SVG mockup of the first page of the 'Sales' report"

### Advanced queries
- "Execute SQL query: SELECT table_name, COUNT(*) as col_count FROM model_column GROUP BY table_name"
- "How many DAX measures are there in total?"

---

## 🔧 Troubleshooting

### MCP doesn't connect
1. Verify that the path in the configuration is absolute
2. Make sure `mcp_server.py` exists at that location
3. Completely restart the application (not just reload)
4. Check logs in Claude Desktop or VS Code console

### Power BI authentication errors
```
Logout from Power BI and login again
```

### Workspace takes too long to download
This is normal for large workspaces. The advantage of this tool is that it has NO timeouts. Let the process finish.

---

## 📚 Additional documentation

For more technical information, see:

- [MCP API Documentation](Documentation/MCP_SERVER.md)
- [PBIR and Legacy formats](Documentation/DUAL_FORMAT_SUPPORT.md)
- [Changelog](Documentation/CHANGELOG_EN.md)
- [Detailed setup guide](Documentation/SETUP_MCP_COPILOT.md)

---

## 🤝 Contributions

Contributions are welcome. Please:
1. Fork the project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

---

## 👥 Author

Miguel Egea - [@megeagomez](https://github.com/megeagomez)

---

**Questions or issues?** Open an [issue](https://github.com/megeagomez/SemanticModelGenerator/issues) on GitHub.

#### 1.4 Generate new models based on report needs
```python
subset = model.create_subset_model(
    table_specs=list(columns_used.keys()),
    subset_name="OptimizedModel.SemanticModel",
    recursive=False
)
subset.save_to_directory(Path("D:/globalai/DemoADN/OptimizedModel.SemanticModel"))
```

---

### 2. Using the command line

#### 2.1 Import workspaces from Power BI
```bash
python Importer/src/import_from_powerbi.py --workspace "DemoADN" --db "D:/globalai/datosglobalai.duckdb" --dest "D:/globalai"
```

#### 2.2 Query and document models and reports
```bash
python scripts/inspect_model.py --model "D:/globalai/DemoADN/semanticAdventureworks.SemanticModel"
python scripts/inspect_report.py --report "D:/globalai/beacicd/informe 1.Report"
```

#### 2.3 Create mockups, analyze field usage, and establish lineage

These steps are best performed through **prompts to GitHub Copilot or Claude**:

```
Example prompt 1: "Analyze the report in D:/globalai/beacicd/informe 1.Report and give me a summary of fields used"
Example prompt 2: "Create an SVG mockup of the report pages"
Example prompt 3: "Establish the lineage between report informe 1 and model semanticAdventureworks"
```

The MCP will handle these requests automatically.

#### 2.4 Generate new models based on report needs

Also via prompts:

```
Example prompt: "Create an optimized submodel for report informe 1 that only includes used tables and columns"
```

---

---

---

```bash
# Clone repository
git clone https://github.com/megeagomez/SemanticModelGenerator.git
cd "pyconstelaciones + Reports"

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Windows CMD:
.\.venv\Scripts\activate.bat
# Linux/Mac:
source .venv/bin/activate

# Install dependencies (if any)
# pip install -r requirements.txt
```

## 🔧 Basic Usage

### Load and copy a complete model

```python
from pathlib import Path
from models import SemanticModel

# Load model
source_path = Path("Modelos/FullAdventureWorks.SemanticModel")
model = SemanticModel(str(source_path))
model.load_from_directory(source_path)

# Save copy
target_path = Path("Modelos/CopyModel.SemanticModel")
model.save_to_directory(target_path)
```

### Create a submodel with specific tables

```python
# Create submodel with recursive search
subset = model.create_subset_model(
    table_specs=[
        ("FactInternetSales", "ManyToOne"),  # Include related dimensions
        ("DimProduct", "Both")               # Search in both directions
    ],
    subset_name="SalesModel.SemanticModel",
    recursive=True,
    max_depth=3
)

subset.save_to_directory(Path("Modelos/SalesModel.SemanticModel"))
```

### Filter columns and measures

```python
from models import TableElementSpec

# Define which elements to include/exclude
element_specs = {
    "FactInternetSales": TableElementSpec(
        columns=["SalesAmount", "OrderQuantity"],
        measures=["Total Sales"],
        mode='include'  # Only include these elements
    ),
    "DimCustomer": TableElementSpec(
        columns=["Phone", "EmailAddress"],
        mode='exclude'  # Exclude these elements
    )
}

subset = model.create_subset_model(
    table_specs=["FactInternetSales", "DimCustomer"],
    subset_name="FilteredModel.SemanticModel",
    table_elements=element_specs
)
```

### Analyze reports and create usage-based submodel

```python
from models import clsReport
from collections import defaultdict

# Analyze all reports
all_references = defaultdict(set)
for report_dir in Path("Modelos").glob("*.Report"):
    report = clsReport(str(report_dir))
    references = report.get_all_columns_used()
    
    for table, columns in references.items():
        all_references[table].update(columns)

# Create submodel with only tables/columns used in reports
element_specs = {
    table: TableElementSpec(columns=list(columns), mode='include')
    for table, columns in all_references.items()
}

subset = model.create_subset_model(
    table_specs=list(all_references.keys()),
    subset_name="ReportBasedModel.SemanticModel",
    recursive=False,  # Only explicit tables
    table_elements=element_specs
)
```

## 📚 Documentation

Complete documentation is available in the [`Documentation/`](Documentation/) folder:

- [Main README](Documentation/README.md) - Class schema and examples
- [SemanticModel](Documentation/SemanticModel.md) - Main class for models
- [Report](Documentation/Report.md) - Power BI report analysis
- [Table](Documentation/Table.md) - Table management
- [Relationship](Documentation/Relationship.md) - Table relationships
- [Model](Documentation/Model.md) - Model properties
- [Culture](Documentation/Culture.md) - Cultures/languages
- [Platform](Documentation/Platform.md) - Platform configuration
- [Definition](Documentation/Definition.md) - Model definition
- [TmdlParser](Documentation/TmdlParser.md) - TMDL format parser
- [MCP_SERVER](Documentation/MCP_SERVER.md) - Claude Desktop integration
- [PROMPTS_HISTORY](Documentation/PROMPTS_HISTORY.md) - Development history

## 🎯 Use Cases

1. **Create business area-derived models**: Extract only tables related to sales, finance, etc.
2. **Optimize models for specific reports**: Include only columns/measures actually used
3. **Dependency analysis**: Discover which reports use which tables and columns
4. **Migrations and copies**: Duplicate models while maintaining structure and metadata
5. **Model cleanup**: Remove unused columns while preserving relationships

## 🔑 Key Concepts

### Search Direction vs Cardinality

- **Search direction** (`ManyToOne`, `OneToMany`, `Both`): Controls which related tables are included in the submodel
- **Relationship cardinality**: Property of each relationship that is preserved intact (not modified)

### Integrity Preservation

- **Foreign key columns** are automatically included if they participate in relationships
- **Partitions** are always preserved (mandatory)
- All **attributes and properties** remain intact

## 📝 Complete Example

See [`InmonMode.py`](InmonMode.py) for complete examples of:
- Complete model copying
- Submodels with search directions
- Element filtering by table
- Report analysis and optimized submodel creation

## 🤝 Contributions

Contributions are welcome. Please:
1. Fork the repository
2. Create a branch for your feature (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ✨ Author

Miguel Egea

## 🙏 Acknowledgments

Developed with the assistance of GitHub Copilot and Claude AI.
