"""
Test del DaxTokenizer contra datos reales de gc.duckdb.
"""

import sys
from pathlib import Path

# Asegurar que el paquete models está accesible
sys.path.insert(0, str(Path(__file__).resolve().parent))

from models.dax_tokenizer import DaxTokenizer, DaxDependencies

DB_PATH = r"D:\mcpdata\testgc\gc.duckdb"


def test_basic_expressions():
    """Tests con expresiones DAX conocidas (sin DB)."""

    known_tables = {"Fact_Pedidos", "Dim_Clientes", "Dim_Productos", "dim_WorkingDay"}
    known_measures = {
        "# Pedidos": "COUNTROWS(Fact_Pedidos)",
        "#Pedidos AA": "CALCULATE([# Pedidos], SAMEPERIODLASTYEAR(dim_WorkingDay[Fecha]))",
        "MoM% Pedidos": "DIVIDE([# Pedidos] - [#Pedidos AA], [#Pedidos AA]*100)",
        "# pedidos Calientes": "CALCULATE([# Pedidos], Dim_Estados_Pedido[BK_id_estado_Pedido]=1)",
        "ConteoClientes": "DISTINCTCOUNT(Dim_Clientes[CodigoCliente])",
    }
    known_columns = {
        "Fact_Pedidos": {"IdPedido", "Fecha"},
        "Dim_Clientes": {"CodigoCliente", "Nombre"},
        "dim_WorkingDay": {"Fecha", "Es_Mes_actual", "key"},
    }

    tk = DaxTokenizer(known_tables, known_measures, known_columns)

    # Test 1: Simple COUNTROWS
    print("=" * 60)
    print("TEST 1: COUNTROWS(Fact_Pedidos)")
    deps = tk.analyze("COUNTROWS(Fact_Pedidos)")
    print(f"  Tablas:    {deps.tables}")
    print(f"  Columnas:  {deps.columns}")
    print(f"  Medidas:   {deps.measures}")
    print(f"  Funciones: {deps.functions}")
    assert "COUNTROWS" in deps.functions
    # Note: Fact_Pedidos here is a function argument, not Table[Col] - may or may not be detected
    print("  ✓ OK")

    # Test 2: Measure reference + table[col]
    print("\nTEST 2: CALCULATE([# Pedidos], Dim_Estados_Pedido[BK_id_estado_Pedido]=1)")
    deps = tk.analyze("CALCULATE([# Pedidos], Dim_Estados_Pedido[BK_id_estado_Pedido]=1)")
    print(f"  Tablas:    {deps.tables}")
    print(f"  Columnas:  {deps.columns}")
    print(f"  Medidas:   {deps.measures}")
    print(f"  Funciones: {deps.functions}")
    assert "# Pedidos" in deps.measures
    assert "CALCULATE" in deps.functions
    assert "Dim_Estados_Pedido" in deps.tables
    print("  ✓ OK")

    # Test 3: Chained measure references
    print("\nTEST 3: DIVIDE([# Pedidos] - [#Pedidos AA], [#Pedidos AA]*100)")
    deps = tk.analyze("DIVIDE([# Pedidos] - [#Pedidos AA], [#Pedidos AA]*100)")
    print(f"  Tablas:    {deps.tables}")
    print(f"  Columnas:  {deps.columns}")
    print(f"  Medidas:   {deps.measures}")
    print(f"  Funciones: {deps.functions}")
    assert "# Pedidos" in deps.measures
    assert "#Pedidos AA" in deps.measures
    assert "DIVIDE" in deps.functions
    print("  ✓ OK")

    # Test 4: VAR expression
    print("\nTEST 4: VAR + RETURN expression")
    expr = """
    VAR EsMesCerrado = IF(MAX(dim_WorkingDay[Es_Mes_actual])="No", TRUE(), FALSE())
    VAR resultado = [# Pedidos]
    RETURN resultado
    """
    deps = tk.analyze(expr)
    print(f"  Tablas:    {deps.tables}")
    print(f"  Columnas:  {deps.columns}")
    print(f"  Medidas:   {deps.measures}")
    print(f"  Funciones: {deps.functions}")
    print(f"  Variables: {deps.variables}")
    assert "EsMesCerrado" in deps.variables
    assert "resultado" in deps.variables
    assert "dim_WorkingDay" in deps.tables
    assert "# Pedidos" in deps.measures
    print("  ✓ OK")

    # Test 5: Transitive resolution
    print("\nTEST 5: Transitive resolution")
    all_deps = tk.analyze_all_measures()
    resolved = tk.resolve_transitive_measures(all_deps)
    mom = resolved.get("MoM% Pedidos")
    if mom:
        print(f"  MoM% Pedidos → tablas:   {mom.tables}")
        print(f"  MoM% Pedidos → columnas: {mom.columns}")
        print(f"  MoM% Pedidos → medidas:  {mom.measures}")
        print(f"  MoM% Pedidos → funcs:    {mom.functions}")
        # MoM% usa [# Pedidos] y [#Pedidos AA]
        # [# Pedidos] usa COUNTROWS(Fact_Pedidos) → no table[col]
        # [#Pedidos AA] usa CALCULATE([# Pedidos], SAMEPERIODLASTYEAR(dim_WorkingDay[Fecha]))
        #   → dim_WorkingDay[Fecha] + transitivamente # Pedidos's deps
        assert "dim_WorkingDay" in mom.tables
        assert "# Pedidos" in mom.measures
        assert "#Pedidos AA" in mom.measures
    print("  ✓ OK")

    # Test 6: Quoted table name
    print("\nTEST 6: Quoted table reference 'My Table'[Column]")
    deps = tk.analyze("CALCULATE(SUM('My Table'[Amount]), 'Other Table'[Year] = 2024)")
    print(f"  Tablas:    {deps.tables}")
    print(f"  Columnas:  {deps.columns}")
    assert "My Table" in deps.tables
    assert "Other Table" in deps.tables
    assert "Amount" in deps.columns.get("My Table", set())
    assert "Year" in deps.columns.get("Other Table", set())
    print("  ✓ OK")

    print("\n" + "=" * 60)
    print("All basic tests PASSED!")
    print("=" * 60)


def test_from_duckdb():
    """Test cargando datos reales desde gc.duckdb."""

    print("\n" + "=" * 60)
    print("TEST FROM DUCKDB")
    print("=" * 60)

    db = Path(DB_PATH)
    if not db.exists():
        print(f"  ⚠ Base de datos no encontrada: {DB_PATH}")
        print("  Skipping DuckDB tests.")
        return

    tk, measure_table_map = DaxTokenizer.from_duckdb(DB_PATH)

    print(f"  Tablas conocidas:  {len(tk.known_tables)}")
    print(f"  Medidas conocidas: {len(tk.known_measures)}")
    print(f"  Columnas tablas:   {len(tk.known_columns)}")

    # Analyze all measures
    all_deps = tk.analyze_all_measures()
    print(f"  Medidas analizadas: {len(all_deps)}")

    # Stats
    total_table_refs = sum(len(d.tables) for d in all_deps.values())
    total_measure_refs = sum(len(d.measures) for d in all_deps.values())
    total_functions = sum(len(d.functions) for d in all_deps.values())
    total_variables = sum(len(d.variables) for d in all_deps.values())

    print(f"\n  Resumen directo:")
    print(f"    Total refs a tablas:  {total_table_refs}")
    print(f"    Total refs a medidas: {total_measure_refs}")
    print(f"    Total funciones DAX:  {total_functions}")
    print(f"    Total variables VAR:  {total_variables}")

    # Show a few examples
    print(f"\n  Primeras 5 medidas con dependencias:")
    count = 0
    for name, deps in all_deps.items():
        if deps.tables or deps.measures:
            print(f"\n    [{measure_table_map.get(name, '?')}]::{name}")
            if deps.tables:
                print(f"      → Tablas:  {deps.tables}")
            if deps.columns:
                for t, cols in deps.columns.items():
                    print(f"      → {t}[{', '.join(cols)}]")
            if deps.measures:
                print(f"      → Medidas: {deps.measures}")
            if deps.functions:
                print(f"      → Funcs:   {deps.functions}")
            count += 1
            if count >= 5:
                break

    # Transitive resolution
    print(f"\n  Resolviendo dependencias transitivas...")
    resolved = tk.resolve_transitive_measures(all_deps)

    # Find measure with most transitive deps
    most_deps = max(resolved.items(), key=lambda x: len(x[1].tables) + len(x[1].measures))
    name = most_deps[0]
    deps = most_deps[1]
    print(f"\n  Medida con más dependencias transitivas: {name}")
    print(f"    Tabla: {measure_table_map.get(name, '?')}")
    print(f"    Tablas ({len(deps.tables)}):  {deps.tables}")
    print(f"    Medidas ({len(deps.measures)}): {deps.measures}")
    print(f"    Funciones ({len(deps.functions)}): {deps.functions}")

    # Table dependency graph
    print(f"\n  Grafo de dependencias entre tablas:")
    table_dep_graph = tk.get_table_dependencies(resolved, measure_table_map)
    for tbl, dep_tables in sorted(table_dep_graph.items()):
        if dep_tables:
            print(f"    {tbl} → {dep_tables}")

    print(f"\n  Total tablas con dependencias: {len(table_dep_graph)}")
    print("=" * 60)
    print("DuckDB test completed!")


def test_clean_expression():
    """Test que la limpieza de lineageTag funciona."""
    print("\nTEST: _clean_expression")

    tk = DaxTokenizer()
    expr = """COUNTROWS(Fact_Pedidos)+0
lineageTag: 202b6e17-9733-4916-bba3-22db5b430ce3"""
    deps = tk.analyze(expr)
    print(f"  Funciones: {deps.functions}")
    assert "COUNTROWS" in deps.functions
    # lineageTag no debería interferir
    print("  ✓ OK")


def test_save_dependencies_to_db():
    """Test save_dependencies_to_db contra gc.duckdb."""
    import duckdb

    print("\n" + "=" * 60)
    print("TEST: save_dependencies_to_db")
    print("=" * 60)

    db = Path(DB_PATH)
    if not db.exists():
        print(f"  ⚠ Base de datos no encontrada: {DB_PATH}")
        return

    tk, measure_table_map = DaxTokenizer.from_duckdb(DB_PATH)
    inserted = tk.save_dependencies_to_db(DB_PATH, measure_table_map=measure_table_map)
    print(f"  Filas insertadas: {inserted}")

    # Verificar contenido
    conn = duckdb.connect(DB_PATH, read_only=True)
    try:
        total = conn.execute(
            "SELECT COUNT(*) FROM semantic_model_measure_dependencies"
        ).fetchone()[0]
        print(f"  Total filas en tabla: {total}")
        assert total == inserted

        by_type = conn.execute(
            "SELECT dependency_type, COUNT(*) "
            "FROM semantic_model_measure_dependencies "
            "GROUP BY dependency_type ORDER BY dependency_type"
        ).fetchall()
        for dtype, cnt in by_type:
            print(f"    {dtype}: {cnt}")

        print("\n  Ejemplo (primeras 10 filas):")
        sample = conn.execute(
            "SELECT measure_name, dependency_type, referenced_name, referenced_table "
            "FROM semantic_model_measure_dependencies LIMIT 10"
        ).fetchall()
        for row in sample:
            print(f"    {row[0]} → [{row[1]}] {row[2]}"
                  + (f" (tabla: {row[3]})" if row[3] else ""))
    finally:
        conn.close()

    print("  ✓ OK")
    print("=" * 60)


if __name__ == "__main__":
    test_basic_expressions()
    test_clean_expression()
    test_from_duckdb()
    test_save_dependencies_to_db()
