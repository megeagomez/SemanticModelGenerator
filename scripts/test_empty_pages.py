"""
Script de prueba para verificar que report.json no contiene 'pages' vacío
"""
from pathlib import Path
import json
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server import PowerBIModelServer

# Crear instancia del servidor con la ruta correcta
models_path = Path(r"d:\Python apps\pyconstelaciones + Reports\Modelos")
server = PowerBIModelServer(models_path)

# Crear un modelo mínimo de prueba
import asyncio
import tempfile
import shutil

async def test_empty_pages():
    """Verifica que report.json no tenga 'pages' cuando está vacío"""
    
    test_model_name = "TestEmptyReport.SemanticModel"
    report_name = "TestEmptyReport.Report"
    
    model_dir = server.models_path / test_model_name
    report_dir = server.models_path / report_name
    
    # Limpiar si existen
    if model_dir.exists():
        shutil.rmtree(model_dir)
    if report_dir.exists():
        shutil.rmtree(report_dir)
    
    try:
        # Crear el report vacío
        await server._scaffold_empty_report_and_pbip(test_model_name)
        
        # Leer el report.json
        report_json_path = report_dir / "definition" / "report.json"
        with open(report_json_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        print("Verificación de report.json después de crear modelo vacío:")
        print(f"  ✓ Archivo creado: {report_json_path.exists()}")
        print(f"  Contiene clave 'pages': {'pages' in report_data}")
        
        if 'pages' in report_data:
            print(f"  ✗ ERROR: 'pages' no debería estar en report.json")
            print(f"    Valor de 'pages': {report_data['pages']}")
        else:
            print(f"  ✓ Correcto: 'pages' no está en report.json")
        
        # Ahora simular merge de reportes (que debería mantener report.json sin 'pages')
        print("\nMerge de reportes (sin reportes origen):")
        await server._copy_and_merge_report_pages([], report_name)
        
        # Leer nuevamente
        with open(report_json_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        print(f"  Contiene clave 'pages': {'pages' in report_data}")
        if 'pages' in report_data:
            print(f"  ✗ ERROR: 'pages' no debería estar después del merge")
        else:
            print(f"  ✓ Correcto: 'pages' sigue sin estar en report.json")
        
    finally:
        # Limpiar
        if model_dir.exists():
            shutil.rmtree(model_dir)
        if report_dir.exists():
            shutil.rmtree(report_dir)

# Ejecutar test
asyncio.run(test_empty_pages())
