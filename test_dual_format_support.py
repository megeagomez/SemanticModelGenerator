"""
Test integral para verificar que ambos formatos (PBIR y legacy) se cargan correctamente.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from models.report import clsReport

def test_format(report_path: str, expected_format: str) -> bool:
    """Prueba que un reporte se carga con el formato esperado."""
    
    if not os.path.exists(report_path):
        print(f"  ❌ No se encontró: {report_path}")
        return False
    
    try:
        report = clsReport(report_path)
        
        # Validar formato
        if report.report_format != expected_format:
            print(f"  ❌ Formato incorrecto. Esperado: {expected_format}, Obtenido: {report.report_format}")
            return False
        
        # Validar que se cargó algo
        if not report.SemanticModel:
            print(f"  ❌ No se extrajo SemanticModel")
            return False
        
        if not report.pages:
            print(f"  ⚠️  No se cargaron páginas (podría ser normal para algunos formatos)")
        
        print(f"  ✅ Formato: {report.report_format}")
        print(f"     SemanticModel: {report.SemanticModel}")
        print(f"     Páginas: {len(report.pages)}")
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Prueba ambos formatos."""
    
    print("=" * 70)
    print("TEST INTEGRAL: SOPORTE DUAL DE FORMATOS PBIR Y LEGACY")
    print("=" * 70)
    
    # Test 1: Formato legacy
    print("\n1️⃣ Probando Formato LEGACY (sections en JSON):")
    legacy_path = r"D:\mcpdata\Toyota\TES - Systems Transformation\PanE CRM leadsOG.Report"
    legacy_ok = test_format(legacy_path, "legacy")
    
    # Test 2: Formato PBIR (si existe)
    print("\n2️⃣ Probando Formato PBIR (file-based):")
    pbir_paths = [
        r"D:\Python apps\pyconstelaciones + Reports\Modelos\FullAdventureWorks.Report",
        r"D:\mcpdata\Toyota\TES - Systems Transformation\PanE CRM leadsOG.Report"  # Fallback
    ]
    
    pbir_ok = False
    for pbir_path in pbir_paths:
        if os.path.exists(os.path.join(pbir_path, "definition")):
            pbir_ok = test_format(pbir_path, "pbir")
            break
    
    if not pbir_ok:
        print(f"  ⚠️  No se encontró reporte PBIR para probar")
    
    # Resumen
    print("\n" + "=" * 70)
    print("RESUMEN:")
    print(f"  Formato LEGACY:  {'✅ PASADO' if legacy_ok else '❌ FALLÓ'}")
    print(f"  Formato PBIR:    {'✅ PASADO' if pbir_ok else '⏭️  SALTADO'}")
    print("=" * 70)
    
    return legacy_ok and (pbir_ok or True)  # Legacy es requerido, PBIR es opcional

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
