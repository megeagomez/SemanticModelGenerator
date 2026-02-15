#!/usr/bin/env python3
"""
Test para verificar que clsReport inicializa correctamente el atributo filters
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from models.report import clsReport

print("=" * 70)
print("TEST: Verificar que clsReport tiene atributo 'filters'")
print("=" * 70)

# Crear una instancia con un directorio que no existe (solo para probar inicialización)
try:
    report = clsReport("/path/que/no/existe")
    
    # Verificar que los atributos existen
    assert hasattr(report, 'filters'), "Falta atributo 'filters'"
    assert isinstance(report.filters, list), "filters no es una lista"
    
    # Verificar que allfilters también existe (para compatibilidad)
    assert hasattr(report, 'allfilters'), "Falta atributo 'allfilters'"
    assert isinstance(report.allfilters, list), "allfilters no es una lista"
    
    print("✅ clsReport tiene atributo 'filters' inicializado correctamente")
    print(f"   filters = {report.filters} (vacía)")
    print(f"   allfilters = {report.allfilters} (vacía)")
    
except Exception as e:
    print(f"❌ Error al crear clsReport: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ TEST PASADO - clsReport está correctamente inicializado")
print("=" * 70)
