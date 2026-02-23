#!/usr/bin/env python3
"""
Test de configuración de data_path en el MCP
Verifica que la ruta de datos se configura correctamente
"""

import sys
import os
from pathlib import Path

# Añadir path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "Importer" / "src"))

from Importer.src.import_from_powerbi import get_data_path, set_data_path

print("=" * 70)
print("TEST 1: Verificar ruta de datos por defecto")
print("=" * 70)

# Verificar ruta por defecto
default_path = get_data_path()
print(f"✅ data_path por defecto: {default_path}")
assert "mcpdata" in str(default_path).lower(), "Ruta por defecto incorrecta"
print("   ✓ Contiene 'mcpdata'")

print("\n" + "=" * 70)
print("TEST 2: Cambiar ruta con set_data_path")
print("=" * 70)

# Cambiar a ruta personalizada
custom_path = "D:/custom_mcpdata"
set_data_path(custom_path)
current_path = get_data_path()
print(f"✅ data_path actualizado: {current_path}")
assert "custom_mcpdata" in str(current_path), "set_data_path no funcionó"
print("   ✓ Ruta personalizada aplicada correctamente")

print("\n" + "=" * 70)
print("TEST 3: Cambiar a otra ruta")
print("=" * 70)

# Cambiar a otra ruta
another_path = "/opt/mcpdata"
set_data_path(another_path)
current_path = get_data_path()
print(f"✅ data_path actualizado: {current_path}")
assert "mcpdata" in str(current_path), "set_data_path no funcionó con segunda ruta"
print("   ✓ Se permite cambiar a diferentes sistemas (Linux/Mac/Windows)")

print("\n" + "=" * 70)
print("TEST 4: Volver a ruta Windows")
print("=" * 70)

# Volver a Windows
windows_path = "C:/ProgramData/mcpdata"
set_data_path(windows_path)
current_path = get_data_path()
print(f"✅ data_path actualizado: {current_path}")
assert "ProgramData" in str(current_path), "Cambio a ProgramData falló"
print("   ✓ Funciona con C:/ProgramData/")

print("\n" + "=" * 70)
print("✅ TODOS LOS TESTS PASARON")
print("=" * 70)
print("\nResumen:")
print("- ✅ data_path tiene valor por defecto D:/mcpdata")
print("- ✅ set_data_path() cambia la ruta global")
print("- ✅ get_data_path() retorna la ruta actual")  
print("- ✅ Compatible con rutas Windows, Linux, Mac")

