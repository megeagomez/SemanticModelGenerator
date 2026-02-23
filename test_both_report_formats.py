#!/usr/bin/env python3
"""
Test para verificar que clsReport maneja ambos formatos:
1. Formato PBIR (nuevo): definition/report.json
2. Formato antiguo: report.json en raíz
"""

import sys
import os
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from models.report import clsReport

print("=" * 70)
print("TEST: Verificar detección de ambos formatos de reporte")
print("=" * 70)

# Probar con un reporte antiguo que tengamos
test_report_path = r"D:\mcpdata\Toyota\TES - Systems Transformation\PanE CRM leadsOG.Report"

if os.path.exists(test_report_path):
    print(f"\n✅ Encontrado reporte de test: {test_report_path}")
    
    # Verificar estructura
    print("\nEstructura del reporte:")
    for item in os.listdir(test_report_path):
        item_path = os.path.join(test_report_path, item)
        item_type = "carpeta" if os.path.isdir(item_path) else "archivo"
        print(f"  - {item} ({item_type})")
    
    # Crear instancia de clsReport
    print("\n📄 Intentando parsear...")
    try:
        report = clsReport(test_report_path)
        
        print(f"\n✅ Reporte parseado exitosamente!")
        print(f"   - report_path: {report.report_path}")
        print(f"   - pages_path: {report.pages_path}")
        print(f"   - SemanticModel: {report.SemanticModel}")
        print(f"   - semantic_model_id: {report.semantic_model_id}")
        print(f"   - Total páginas: {len(report.pages)}")
        
        if report.report_path:
            print(f"\n✅ report.json detectado correctamente")
            print(f"   Formato: {'PBIR (definition/)' if 'definition' in report.report_path else 'Antiguo (raíz)'}")
        
        if report.pages_path:
            print(f"\n✅ Carpeta de páginas detectada: {report.pages_path}")
        else:
            print(f"\n⚠️ No se encontró carpeta de páginas")
            
    except Exception as e:
        print(f"❌ Error al parsear: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"\n⚠️ No se encontró reporte de test en: {test_report_path}")
    print("   Directorios disponibles en mcpdata:")
    mcpdata_path = r"D:\mcpdata\Toyota"
    if os.path.exists(mcpdata_path):
        for item in os.listdir(mcpdata_path):
            item_path = os.path.join(mcpdata_path, item)
            if os.path.isdir(item_path):
                print(f"     - {item}/")

print("\n" + "=" * 70)
print("TEST COMPLETADO")
print("=" * 70)
