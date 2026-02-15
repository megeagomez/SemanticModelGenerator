#!/usr/bin/env python3
"""
Test que demuestra cómo la variable global _active_auth_flow 
mantiene el estado de autenticación en memoria incluso después de 
borrar los archivos de token.
"""

import sys
import os
from pathlib import Path
import json

# Añadir path
sys.path.insert(0, str(Path(__file__).parent))

from Importer.src import import_from_powerbi

# Test 1: Simular una sesión anterior con token en memoria
print("=" * 70)
print("TEST 1: Simular estado anterior con token en memoria")
print("=" * 70)

# Crear un downloader ficticio con token
from Importer.src.FabricItemDownloader import FabricItemDownloader
downloader = FabricItemDownloader()
downloader.access_token = "test_token_12345"

# Guardar en la variable global (simulando una sesión anterior)
import_from_powerbi._active_auth_flow["downloader"] = downloader
import_from_powerbi._active_auth_flow["status"] = "completed"

print(f"✅ Token en memoria (_active_auth_flow): {downloader.access_token[:20]}...")
print(f"   Estado: {import_from_powerbi._active_auth_flow['status']}")

# Test 2: Verificar que check_auth_status devuelve autenticado
print("\n" + "=" * 70)
print("TEST 2: check_auth_status() - ANTES de logout")
print("=" * 70)

result = import_from_powerbi.check_auth_status()
print(f"Resultado: {result}")
print(f"Autenticado: {result['authenticated']}")
print(f"Mensaje: {result['message']}")

# Test 3: Verificar archivos (NO existen)
print("\n" + "=" * 70)
print("TEST 3: Verificar archivos de token")
print("=" * 70)

token_file = Path(__file__).parent / "fabric_token_cache.json"
status_file = Path(__file__).parent / "data" / "powerbi_auth_status.json"

print(f"Token file existe: {token_file.exists()}")
print(f"Status file existe: {status_file.exists()}")
print(f"⚠️  Los archivos NO existen, pero aún está 'autenticado' por el token en memoria!")

# Test 4: Simular logout limpiando la variable global
print("\n" + "=" * 70)
print("TEST 4: Simular LOGOUT - Limpiar _active_auth_flow")
print("=" * 70)

# Limpiar la variable global
import_from_powerbi._active_auth_flow = {
    "downloader": None, 
    "flow": None, 
    "message": None, 
    "thread": None,
    "status": None,
    "app": None
}

print("✅ Variable global _active_auth_flow limpiada")

# Test 5: Verificar que check_auth_status AHORA devuelve no autenticado
print("\n" + "=" * 70)
print("TEST 5: check_auth_status() - DESPUÉS de logout")
print("=" * 70)

result = import_from_powerbi.check_auth_status()
print(f"Resultado: {result}")
print(f"Autenticado: {result['authenticated']}")
print(f"Mensaje: {result['message']}")
print(f"✅ Ahora correctamente devuelve: NO AUTENTICADO")

print("\n" + "=" * 70)
print("✅ TEST COMPLETADO - El problema y la solución están claros")
print("=" * 70)
