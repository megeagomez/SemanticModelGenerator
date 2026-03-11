"""
SQL Query Tool para DuckDB
Permite ejecutar queries interactivamente o ver estadísticas de tablas.
"""

import duckdb
import argparse
import sys
import os
from pathlib import Path
from tabulate import tabulate

def print_table(rows, headers=None):
    """Imprime resultados en formato tabla"""
    if not rows:
        print("Sin resultados.")
        return
    
    if headers is None and rows:
        # Si son tuples namedtuple con atributos
        try:
            headers = list(rows[0].keys())
            data = [list(row.values()) for row in rows]
        except (AttributeError, TypeError):
            # Si son tuples simples
            headers = [f"Col{i+1}" for i in range(len(rows[0]))]
            data = rows
    else:
        data = rows
    
    print(tabulate(data, headers=headers, tablefmt="grid"))

def interactive_mode(db_path):
    """Modo interactivo para ejecutar queries"""
    try:
        conn = duckdb.connect(db_path,True)
        print(f"✅ Conectado a: {db_path}")
        print("Escribe 'quit()' o 'exit()' para salir.\n")
        
        while True:
            try:
                query = input("SQL> ").strip()
                
                if not query:
                    continue
                
                if query.lower() in ['quit()', 'exit()', 'quit', 'exit']:
                    print("Hasta luego!")
                    break
                
                # Ejecutar query
                result = conn.execute(query).fetchall()
                
                # Obtener headers de la descripción
                description = conn.description
                if description:
                    headers = [desc[0] for desc in description]
                    print_table(result, headers=headers)
                else:
                    print(f"Query ejecutado exitosamente. Filas afectadas: {len(result)}")
                
                print()
            
            except Exception as e:
                print(f"❌ Error: {e}\n")
        
        conn.close()
    
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        sys.exit(1)

def show_table_counts(db_path):
    """Muestra el conteo de filas en todas las tablas"""
    try:
        conn = duckdb.connect(db_path, read_only=True)
        print(f"📊 Estadísticas de: {db_path}\n")
        
        # Obtener lista de tablas
        tables_result = conn.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'main'
            ORDER BY table_name
        """).fetchall()
        
        if not tables_result:
            print("No hay tablas en esta base de datos.")
            conn.close()
            return
        
        table_names = [row[0] for row in tables_result]
        
        # Obtener conteos
        data = []
        total_rows = 0
        
        for table_name in table_names:
            try:
                count_result = conn.execute(f"SELECT COUNT(*) as count FROM {table_name}").fetchone()
                count = count_result[0] if count_result else 0
                total_rows += count
                data.append([table_name, count])
            except Exception as e:
                data.append([table_name, f"Error: {str(e)[:30]}"])
        
        print_table(data, headers=["Tabla", "Filas"])
        print(f"\n📈 Total de filas: {total_rows}")
        print(f"📋 Total de tablas: {len(table_names)}")
        
        conn.close()
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Herramienta SQL interactiva para DuckDB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Modo interactivo
  python sql_query.py --db data/powerbi.duckdb
  
  # Ver conteo de tablas
  python sql_query.py --db data/powerbi.duckdb --count
  
  # Si omites --db, usa 'data/powerbi.duckdb' por defecto
  python sql_query.py --count
        """
    )
    
    parser.add_argument(
        "--db",
        type=str,
        help="Ruta a la base de datos DuckDB",
        default="data/powerbi.duckdb"
    )
    
    parser.add_argument(
        "--count",
        action="store_true",
        help="Mostrar conteo de filas en todas las tablas"
    )
    
    args = parser.parse_args()
    
    # Validar que la BD existe
    if not os.path.exists(args.db):
        print(f"❌ Base de datos no encontrada: {args.db}")
        sys.exit(1)
    
    # Ejecutar según modo
    if args.count:
        show_table_counts(args.db)
    else:
        interactive_mode(args.db)

if __name__ == "__main__":
    main()
