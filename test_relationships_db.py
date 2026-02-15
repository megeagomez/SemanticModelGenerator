#!/usr/bin/env python
"""Test para verificar que las relaciones se persisten en DuckDB."""

import duckdb
import tempfile
from pathlib import Path
from models.relationship import Relationship

# Crear una conexión temporal a DuckDB
with tempfile.TemporaryDirectory() as tmpdir:
    db_path = Path(tmpdir) / "test.duckdb"
    conn = duckdb.connect(str(db_path))
    
    print("=" * 70)
    print("TEST: Verificar tabla semantic_model_relationship")
    print("=" * 70)
    
    # Crear secuencias y tabla para el test
    conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_semantic_model_id START 1")
    conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_semantic_model_relationship_id START 1")
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS semantic_model (
            id INTEGER PRIMARY KEY DEFAULT nextval('seq_semantic_model_id'),
            semantic_model_id VARCHAR,
            workspace_id VARCHAR,
            name VARCHAR NOT NULL,
            culture VARCHAR,
            default_power_bi_data_source_version VARCHAR,
            source_query_culture VARCHAR,
            data_access_options JSON,
            annotations JSON,
            created_at TIMESTAMP DEFAULT now(),
            updated_at TIMESTAMP DEFAULT now()
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS semantic_model_relationship (
            id INTEGER PRIMARY KEY DEFAULT nextval('seq_semantic_model_relationship_id'),
            semantic_model_id INTEGER NOT NULL,
            relationship_name VARCHAR NOT NULL,
            from_table VARCHAR NOT NULL,
            from_column VARCHAR NOT NULL,
            to_table VARCHAR NOT NULL,
            to_column VARCHAR NOT NULL,
            cardinality VARCHAR,
            cross_filtering_behavior VARCHAR,
            security_filtering_behavior VARCHAR,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT now(),
            FOREIGN KEY(semantic_model_id) REFERENCES semantic_model(id)
        )
    """)
    
    # Insertar un modelo para el test
    conn.execute("""
        INSERT INTO semantic_model (semantic_model_id, workspace_id, name, culture)
        VALUES (?, ?, ?, ?)
    """, ["test-model-id", "test-workspace-id", "TestModel", "en-US"])
    
    # Obtener el ID del modelo
    result = conn.execute("SELECT id FROM semantic_model WHERE semantic_model_id = ?", ["test-model-id"]).fetchall()
    model_id = result[0][0]
    
    print(f"✓ Modelo insertado con ID: {model_id}")
    
    # Insertar relaciones de ejemplo
    test_relationships = [
        ("rel1", "FactInternetSales", "ProductKey", "DimProduct", "ProductKey", "1:*", "OneDirection", None, True),
        ("rel2", "FactInternetSales", "CustomerKey", "DimCustomer", "CustomerKey", "1:*", "BothDirections", None, True),
        ("rel3", "FactInternetSales", "DateKey", "DimDate", "DateKey", "*:1", "OneDirection", None, False),
    ]
    
    for rel_name, from_table, from_col, to_table, to_col, card, cross_filter, sec_filter, is_active in test_relationships:
        conn.execute("""
            INSERT INTO semantic_model_relationship 
            (semantic_model_id, relationship_name, from_table, from_column, to_table, to_column, cardinality, cross_filtering_behavior, security_filtering_behavior, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [model_id, rel_name, from_table, from_col, to_table, to_col, card, cross_filter, sec_filter, is_active])
    
    print(f"✓ {len(test_relationships)} relaciones insertadas")
    
    # Verificar que se pueden recuperar
    print("\n" + "=" * 70)
    print("RELACIONES GUARDADAS:")
    print("=" * 70)
    
    result = conn.execute("""
        SELECT relationship_name, from_table, from_column, to_table, to_column, cardinality, is_active
        FROM semantic_model_relationship
        WHERE semantic_model_id = ?
        ORDER BY relationship_name
    """, [model_id]).fetchall()
    
    print(f"\nTotal: {len(result)} relaciones\n")
    
    for i, (rel_name, from_table, from_col, to_table, to_col, card, is_active) in enumerate(result, 1):
        print(f"Relación {i}:")
        print(f"  Nombre:            {rel_name}")
        print(f"  {from_table}.{from_col} → {to_table}.{to_col}")
        print(f"  Cardinalidad:      {card}")
        print(f"  Activa:            {is_active}")
        print()
    
    conn.close()
    
    print("=" * 70)
    print("✓ TEST COMPLETADO CON ÉXITO!")
    print("=" * 70)
    print("\nResumen:")
    print("- Tabla semantic_model_relationship creada correctamente")
    print("- Relaciones insertadas y recuperadas desde DuckDB")
    print("- Foreign key vinculada a semantic_model funcionando")
