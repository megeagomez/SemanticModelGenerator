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
- [MCP_SERVER](MCP_SERVER.md) - Claude Desktop integration
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
