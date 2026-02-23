#!/usr/bin/env python
"""Test para verificar que el filtro de Ventas se parsea correctamente."""

from models.report import Filter

# JSON del visual que proporcionó el usuario
sample_filter_config = {
    "filters": [
        {
            "name": "8c290f3f18804e5feadf",
            "field": {
                "Aggregation": {
                    "Expression": {
                        "Column": {
                            "Expression": {
                                "SourceRef": {
                                    "Entity": "FactInternetSales"
                                }
                            },
                            "Property": "OrderQuantity"
                        }
                    },
                    "Function": 0
                }
            },
            "type": "Advanced"
        },
        {
            "name": "648acce11e80d900170a",
            "field": {
                "Column": {
                    "Expression": {
                        "SourceRef": {
                            "Entity": "DimCurrency"
                        }
                    },
                    "Property": "CurrencyName"
                }
            },
            "type": "Categorical"
        },
        {
            "name": "07c10847f653e9c3c76f",
            "field": {
                "Measure": {
                    "Expression": {
                        "SourceRef": {
                            "Entity": "FactInternetSales"
                        }
                    },
                    "Property": "Ventas"
                }
            },
            "type": "Advanced",
            "filter": {
                "Version": 2,
                "From": [
                    {
                        "Name": "f",
                        "Entity": "FactInternetSales",
                        "Type": 0
                    }
                ],
                "Where": [
                    {
                        "Condition": {
                            "Comparison": {
                                "ComparisonKind": 1,
                                "Left": {
                                    "Measure": {
                                        "Expression": {
                                            "SourceRef": {
                                                "Source": "f"
                                            }
                                        },
                                        "Property": "Ventas"
                                    }
                                },
                                "Right": {
                                    "Literal": {
                                        "Value": "0M"
                                    }
                                }
                            }
                        }
                    }
                ]
            },
            "howCreated": "User"
        }
    ]
}

print("=" * 70)
print("TEST: Parsear filtros complejos (Column, Aggregation, Measure)")
print("=" * 70)

filters = Filter.extract_from_config(
    sample_filter_config,
    filter_type="visual",
    page_name="TestPage",
    visual_name="TestVisual"
)

print(f"\n✓ Total de filtros extraídos: {len(filters)}")
print()

for i, filter_obj in enumerate(filters, 1):
    print(f"Filtro {i}:")
    print(f"  Nombre:        {filter_obj.name}")
    print(f"  Tabla:         {filter_obj.table_name}")
    print(f"  Campo:         {filter_obj.column_name}")
    print(f"  Tipo Filtro:   {filter_obj.filter_type}")
    print(f"  Página:        {filter_obj.page_name}")
    print(f"  Visual:        {filter_obj.visual_name}")
    print(f"  Descripción:   {filter_obj.description}")
    print()

# Verificar específicamente el filtro de Ventas
print("=" * 70)
print("VERIFICACIÓN DEL FILTRO DE VENTAS:")
print("=" * 70)

venta_filters = [f for f in filters if "Ventas" in f.column_name]

if venta_filters:
    print(f"✓ Filtro de Ventas ENCONTRADO!")
    for f in venta_filters:
        print(f"  - {f.table_name}.{f.column_name}")
        print(f"    Descripción: {f.description}")
else:
    print("✗ Filtro de Ventas NO ENCONTRADO!")

print("\n" + "=" * 70)
if len(filters) == 3 and venta_filters:
    print("✓ TODOS LOS TESTS PASARON!")
else:
    print(f"✗ PROBLEMAS DETECTADOS: Se esperaban 3 filtros, se encontraron {len(filters)}")
print("=" * 70)
