"""
Test para procesar todos los reports de Toyota y guardarlos en la base de datos.
Procesa reports en modo legacy y extrae columnas, medidas y filtros usados.
"""

import os
import sys
from pathlib import Path
from models.report import clsReport
import duckdb
from datetime import datetime

# Rutas de Toyota
TOYOTA_BASE_PATH = r'D:\mcpdata\toyota'
TOYOTA_DB_PATH = r'D:\mcpdata\toyota\toyota.duckdb'

def find_all_reports(base_path: str) -> list:
    """Busca recursivamente todos los .Report folders en la ruta base."""
    report_folders = []
    for root, dirs, files in os.walk(base_path):
        for dir_name in dirs:
            if dir_name.endswith('.Report'):
                report_path = os.path.join(root, dir_name)
                report_folders.append(report_path)
    return report_folders


def process_report_simple(report_path: str, conn, show_details: bool = False) -> dict:
    """Procesa un report y lo guarda en la base de datos. Retorna estadísticas."""
    stats = {
        'path': report_path,
        'name': os.path.basename(report_path),
        'success': False,
        'format': None,
        'pages': 0,
        'visuals': 0,
        'columns': 0,
        'measures': 0,
        'filters': 0,
        'error': None
    }
    
    try:
        # Cargar el report
        report = clsReport(report_path)
        stats['format'] = report.report_format
        stats['pages'] = len(report.pages)
        
        # Contar visuals
        for page in report.pages:
            stats['visuals'] += len(page.visuals)
        
        # Obtener totales
        all_columns = report.get_all_columns_used()
        all_measures = report.get_all_measures_used()
        stats['columns'] = sum(len(cols) for cols in all_columns.values())
        stats['measures'] = sum(len(meas) for meas in all_measures.values())
        stats['filters'] = len(report.filters)
        
        # Guardar en base de datos
        report.save_to_database(conn)
        stats['success'] = True
        
        if show_details:
            print(f"  [OK] {stats['name']}")
            print(f"       Formato: {stats['format']}, Paginas: {stats['pages']}, Visuals: {stats['visuals']}")
            print(f"       Columnas: {stats['columns']}, Medidas: {stats['measures']}, Filtros: {stats['filters']}")
        
    except Exception as e:
        stats['error'] = str(e)
        if show_details:
            print(f"  [ERROR] {stats['name']}: {str(e)[:100]}")
    
    return stats


def test_single_report(report_path: str):
    """Prueba un único report para ver si se cargan visuals y sus referencias."""
    print(f"\n{'='*80}")
    print(f"Analizando: {os.path.basename(report_path)}")
    print(f"{'='*80}")
    
    try:
        # Cargar el report
        report = clsReport(report_path)
        
        print(f"Formato del report: {report.report_format}")
        print(f"Numero de paginas: {len(report.pages)}")
        
        # Verificar cada página
        for i, page in enumerate(report.pages, 1):
            print(f"\n  Pagina {i}: {page.name}")
            print(f"    Display Name: {page.displayName}")
            print(f"    Numero de visuals: {len(page.visuals)}")
            
            # Verificar cada visual
            for j, visual in enumerate(page.visuals, 1):
                print(f"\n      Visual {j}: {visual.name}")
                print(f"        Tipo: {visual.visualType}")
                print(f"        Columnas usadas: {len(visual.columns_used)}")
                if visual.columns_used:
                    for col in visual.columns_used[:5]:  # Mostrar solo las primeras 5
                        print(f"          - {col}")
                    if len(visual.columns_used) > 5:
                        print(f"          ... y {len(visual.columns_used) - 5} mas")
                else:
                    print(f"          [!] NO HAY COLUMNAS DETECTADAS")
                
                print(f"        Medidas usadas: {len(visual.measures_used)}")
                if visual.measures_used:
                    for meas in visual.measures_used[:5]:  # Mostrar solo las primeras 5
                        print(f"          - {meas}")
                    if len(visual.measures_used) > 5:
                        print(f"          ... y {len(visual.measures_used) - 5} mas")
                else:
                    print(f"          [!] NO HAY MEDIDAS DETECTADAS")
                
                print(f"        Filtros: {len(visual.filters)}")
                if visual.filters:
                    for filt in visual.filters[:3]:
                        print(f"          - {filt.name}: {filt.table_name}.{filt.column_name}")
        
        # Obtener totales
        all_columns = report.get_all_columns_used()
        all_measures = report.get_all_measures_used()
        
        print(f"\n  TOTALES:")
        print(f"    Total columnas unicas: {sum(len(cols) for cols in all_columns.values())}")
        print(f"    Total medidas unicas: {sum(len(meas) for meas in all_measures.values())}")
        print(f"    Total filtros en report: {len(report.filters)}")
        
        return report
        
    except Exception as e:
        print(f"[ERROR] Error al procesar el report: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_save_to_database(report: clsReport, db_path: str = ":memory:"):
    """Prueba guardar el report en la base de datos y verificar las tablas."""
    print(f"\n{'='*80}")
    print("Guardando en base de datos y verificando tablas")
    print(f"{'='*80}")
    
    try:
        conn = duckdb.connect(db_path)
        
        # Guardar el report (sin pasar report_name, usa el de la instancia)
        report.save_to_database(conn)
        
        # Verificar las tablas
        tables_to_check = [
            "report_column_used",
            "report_measure_used",
            "report_filter",
            "report_page_filter",
            "report_visual_filter"
        ]
        
        for table in tables_to_check:
            try:
                result = conn.execute(f"SELECT COUNT(*) as count FROM {table}").fetchone()
                count = result[0] if result else 0
                status = "[OK]" if count > 0 else "[VACIO]"
                print(f"  {status} {table}: {count} registros")
                
                if count > 0:
                    # Mostrar algunos ejemplos
                    samples = conn.execute(f"SELECT * FROM {table} LIMIT 3").fetchall()
                    columns = [desc[0] for desc in conn.execute(f"SELECT * FROM {table} LIMIT 1").description]
                    print(f"      Columnas: {', '.join(columns)}")
                    for sample in samples:
                        print(f"      Ejemplo: {sample}")
            except Exception as e:
                print(f"  [ERROR] Error al verificar {table}: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"[ERROR] Error al guardar en base de datos: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Función principal: procesa todos los reports de Toyota."""
    print("="*80)
    print("CARGA MASIVA: Reports Toyota a Base de Datos")
    print("="*80)
    print(f"Base Path: {TOYOTA_BASE_PATH}")
    print(f"Database:  {TOYOTA_DB_PATH}")
    print(f"Inicio:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Verificar que la ruta base existe
    if not os.path.exists(TOYOTA_BASE_PATH):
        print(f"[ERROR] La ruta no existe: {TOYOTA_BASE_PATH}")
        return
    
    # Buscar todos los .Report en la ruta (recursivamente)
    print("\n[1/4] Buscando reports...")
    report_folders = find_all_reports(TOYOTA_BASE_PATH)
    print(f"      Encontrados {len(report_folders)} reports")
    
    if not report_folders:
        print("[ERROR] No se encontraron reports (.Report folders)")
        return
    
    # Conectar a la base de datos
    print(f"\n[2/4] Conectando a la base de datos...")
    try:
        conn = duckdb.connect(TOYOTA_DB_PATH)
        print(f"      Conectado a: {TOYOTA_DB_PATH}")
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a la base de datos: {e}")
        return
    
    # Procesar todos los reports
    print(f"\n[3/4] Procesando {len(report_folders)} reports...")
    print("-"*80)
    
    all_stats = []
    successful = 0
    failed = 0
    
    for idx, report_path in enumerate(report_folders, 1):
        print(f"\n  [{idx}/{len(report_folders)}] {os.path.basename(report_path)}")
        stats = process_report_simple(report_path, conn, show_details=True)
        all_stats.append(stats)
        
        if stats['success']:
            successful += 1
        else:
            failed += 1
    
    # Cerrar conexión
    conn.close()
    
    # Mostrar resumen final
    print("\n" + "="*80)
    print("[4/4] RESUMEN FINAL")
    print("="*80)
    print(f"Total reports procesados: {len(report_folders)}")
    print(f"  Exitosos: {successful}")
    print(f"  Fallidos:  {failed}")
    
    if successful > 0:
        total_pages = sum(s['pages'] for s in all_stats if s['success'])
        total_visuals = sum(s['visuals'] for s in all_stats if s['success'])
        total_columns = sum(s['columns'] for s in all_stats if s['success'])
        total_measures = sum(s['measures'] for s in all_stats if s['success'])
        
        print(f"\nEstadisticas acumuladas:")
        print(f"  Total paginas:  {total_pages}")
        print(f"  Total visuals:  {total_visuals}")
        print(f"  Total columnas unicas: {total_columns}")
        print(f"  Total medidas unicas:  {total_measures}")
    
    if failed > 0:
        print(f"\nReports con errores:")
        for stat in all_stats:
            if not stat['success']:
                print(f"  - {stat['name']}: {stat['error'][:80]}")
    
    print(f"\nFin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print(f"\nBase de datos actualizada: {TOYOTA_DB_PATH}")


def main_test_mode():
    """Modo test: solo procesa el primer report con detalles completos."""
    print("="*80)
    print("TEST MODE: Verificacion detallada de un report")
    print("="*80)
    
    # Verificar que la ruta existe
    if not os.path.exists(TOYOTA_BASE_PATH):
        print(f"[ERROR] La ruta no existe: {TOYOTA_BASE_PATH}")
        return
    
    # Buscar todos los .Report en la ruta
    report_folders = find_all_reports(TOYOTA_BASE_PATH)
    
    print(f"\nEncontrados {len(report_folders)} reports en total")
    
    if not report_folders:
        print("[ERROR] No se encontraron reports (.Report folders)")
        return
    
    # Probar el primer report con detalles
    print(f"\nProbando el primer report: {os.path.basename(report_folders[0])}")
    report = test_single_report(report_folders[0])
    
    if report:
        # Probar guardado en base de datos (en memoria para testing)
        test_save_to_database(report, db_path=":memory:")


if __name__ == "__main__":
    # Modo por defecto: procesar todos los reports
    # Para modo test detallado, cambiar a: main_test_mode()
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        main_test_mode()
    else:
        main()
