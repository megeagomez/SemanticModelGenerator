# Copilot Instructions for AI Coding Agents

## Project Overview
This project manages Power BI Semantic Models and Reports using a Python backend. It provides tools for creating, analyzing, and optimizing models and reports, with a strong focus on file/folder structure and automation.

## Key Architectural Conventions
- **Models and Reports Location:** All models and reports are stored under the `Modelos/` directory. Each model has a `.SemanticModel` folder, and each report has a `.Report` folder.
- **Model Creation:** When a new model is created, a corresponding `.pbip` file and a `.Report` folder are also created.
- **Report Structure:** For every new model, the report structure (pages, definition, etc.) must be copied from the template in `Modelos/emptyreport.Report`.
- **File Operations:** Use `shutil.copytree` for copying directory structures and `os.makedirs` for creating directories. Always ensure parent directories exist.
- **Naming Conventions:**
  - Model: `<Name>.SemanticModel`
  - Report: `<Name>.Report`
  - PBIP: `<Name>.pbip`

## Workflows
- **Creating a New Model:**
  1. Create the model directory and files under `Modelos/<Name>.SemanticModel`.
  2. Copy the entire structure of `Modelos/emptyreport.Report` to `Modelos/<Name>.Report`.
  3. Update links in the new report to reference the new model.
  4. Create a `<Name>.pbip` file pointing to the new report.
- **Creating a Subset Model:**
  - Subset models also generate a new report using the empty template.
- **Model/Report Analysis:**
  - Use the `clsReport` and `SemanticModel` classes for parsing and analyzing report/model content.

## Integration Points
- **Entry Point:** `mcp_server.py` (class `PowerBIModelServer`)
- **Model Logic:** `models/semantic_model.py`
- **Report Logic:** `models/report.py`

## Best Practices
- Always use the empty report template for new reports.
- Keep all file and directory operations robust (check existence, handle exceptions).
- Maintain clear separation between model and report logic.
- Document new tools and workflows in this file.

## Example: Creating a New Model
```python
import shutil
from pathlib import Path

template = Path('Modelos/emptyreport.Report')
target = Path(f'Modelos/{name}.Report')
shutil.copytree(template, target)
# Update links in definition.pbir, etc.
```

## Updates
- 2024-06: All new models must use the empty report structure as their report template.
