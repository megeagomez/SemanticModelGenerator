# Power BI Semantic Model Management Library

**[Español](README.md) | English**

---

Python library for programmatically manipulating Power BI semantic models (`.SemanticModel` and `.Report` files).

## 🚀 Features

- **Load and save** complete semantic models
- **Create submodels** with intelligent table and relationship filtering
- **Filter elements** (columns, measures, hierarchies) with include/exclude modes
- **Report analysis** (.Report) to extract used columns and measures
- **Generate SVG** from report pages with visuals
- **Preserve metadata** and original properties
- **TMDL support** (Tabular Model Definition Language format)
- **Claude Desktop integration** via MCP server

## 📦 Installation

---



## 📝 Recommended MCP Workflow

You can work with MCP in two ways: **using Python** or **using the command line**. Both methods allow you to import, query, analyze, and generate Power BI models efficiently.

---

### 1. Using Python

#### 1.1 Import workspaces from Power BI
```python
from Importer.src.import_from_powerbi import import_from_powerbi
import_from_powerbi(
    workspace_name="DemoADN",
    db_path="D:/globalai/datosglobalai.duckdb",
    destination_path="D:/globalai"
)
```

#### 1.2 Query and document models and reports
```python
from models import SemanticModel, clsReport
from pathlib import Path
model = SemanticModel("D:/globalai/DemoADN/semanticAdventureworks.SemanticModel")
model.load_from_directory(Path("D:/globalai/DemoADN/semanticAdventureworks.SemanticModel"))
report = clsReport("D:/globalai/beacicd/informe 1.Report")
columns_used = report.get_all_columns_used()
```

#### 1.3 Create mockups, analyze field usage, and establish lineage
```python
visuals = report.get_visuals()
usage = report.get_field_usage_summary()
lineage = report.get_model_lineage()
```

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
```bash
python scripts/mockup_report.py --report "D:/globalai/beacicd/informe 1.Report"
python scripts/field_usage.py --report "D:/globalai/beacicd/informe 1.Report"
python scripts/lineage.py --report "D:/globalai/beacicd/informe 1.Report"
```

#### 2.4 Generate new models based on report needs
```bash
python scripts/create_subset_model.py --model "D:/globalai/DemoADN/semanticAdventureworks.SemanticModel" --columns-used "columns_used.json" --output "D:/globalai/DemoADN/OptimizedModel.SemanticModel"
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
