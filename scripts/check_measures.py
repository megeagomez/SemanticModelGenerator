"""
Script para verificar qué columnas usa cada medida de FactInternetSales
"""
from pathlib import Path
import sys
import re
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.semantic_model import SemanticModel

# Cargar modelo
model_path = Path(r"d:\Python apps\pyconstelaciones + Reports\Modelos\FullAdventureWorks.SemanticModel")
model = SemanticModel(str(model_path))
model.load_from_directory(model_path)

# Obtener FactInternetSales
fact_table = next(t for t in model.tables if t.name == "FactInternetSales")

print("Medidas de FactInternetSales y sus columnas usadas:\n")

for measure in fact_table.measures:
    print(f"Medida: {measure.name}")
    print(f"  Expresión: {measure.expression}")
    
    # Buscar referencias a columnas
    pattern = r'\b([A-Za-z_][A-Za-z0-9_ ]*?)\s*\[\s*([A-Za-z_][A-Za-z0-9_ ]*?)\s*\]'
    matches = re.findall(pattern, measure.expression)
    
    if matches:
        print(f"  Referencias encontradas:")
        for table, column in matches:
            print(f"    - {table}[{column}]")
    else:
        print(f"  Sin referencias a columnas")
    
    print()
