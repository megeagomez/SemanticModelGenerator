#!/usr/bin/env python3
"""
Test para verificar que las particiones se leen correctamente
"""

from pathlib import Path
from models import Table

# Probar con una tabla conocida
table_path = Path("Modelos/FullAdventureWorks.SemanticModel/definition/tables/DimCustomer.tmdl")

print("=" * 80)
print("Probando lectura de particiones...")
print("=" * 80)

table = Table.from_file(table_path)

print(f"\nTabla: {table.name}")
print(f"Columnas: {len(table.columns)}")
print(f"Medidas: {len(table.measures)}")
print(f"Particiones: {len(table.partitions)}")

print("\n" + "=" * 80)
print("Detalles de particiones:")
print("=" * 80)

for partition in table.partitions:
    print(f"\n📊 Partición: {partition.name}")
    print(f"   Tipo: {partition.source_type}")
    print(f"   Modo: {partition.mode}")
    print(f"   Source (primeras 3 líneas):")
    lines = partition.source_expression.split('\n')[:3]
    for line in lines:
        print(f"      {line}")
    if len(partition.source_expression.split('\n')) > 3:
        print(f"      ... ({len(partition.source_expression.split('\n'))} líneas totales)")

print("\n" + "=" * 80)
print("✅ Test completado")
print("=" * 80)
