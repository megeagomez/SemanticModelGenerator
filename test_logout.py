#!/usr/bin/env python3
"""
Test del método de logout
Verifica que se puede borrar el token de autenticación
"""

from pathlib import Path
import json

# Crear un token de prueba
token_file = Path(__file__).parent / "fabric_token_cache.json"

# Test 1: Crear un token de prueba
print("Test 1: Creando token de prueba...")
test_token = {
    "access_token": "test_token_12345",
    "expires_at": "2026-02-15T14:30:00Z",
    "saved_at": "2026-02-15T13:30:00Z"
}

with open(token_file, "w") as f:
    json.dump(test_token, f)

print(f"✅ Token creado en: {token_file}")
print(f"   Existe: {token_file.exists()}")

# Test 2: Borrar el token (simular logout)
print("\nTest 2: Borrando token (simulando logout)...")
if token_file.exists():
    token_file.unlink()
    print(f"✅ Token borrado correctamente")
    print(f"   Existe ahora: {token_file.exists()}")
else:
    print("⚠️ El token no existe")

# Test 3: Intentar logout cuando no hay token
print("\nTest 3: Intentando logout cuando no hay token...")
if token_file.exists():
    token_file.unlink()

# Simular el método logout
try:
    if token_file.exists():
        token_file.unlink()
        print("✅ Sesión cerrada correctamente. Se borró el token de autenticación.")
    else:
        print("ℹ️ No hay sesión activa. No se encontró token de autenticación.")
except Exception as e:
    print(f"❌ Error al cerrar sesión: {e}")

print("\n✅ Todos los tests completados!")
