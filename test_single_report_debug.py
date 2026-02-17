"""
Test para debuggear un report específico: TES - Gestión Comercial
"""

import os
from models.report import clsReport
import duckdb

# Path del report específico
REPORT_PATH = r'D:\mcpdata\toyota\TES - CONCESIONARIOS\TES - Gestión Comercial.Report'
DB_PATH = r'D:\mcpdata\toyota\toyota.duckdb'

def main():
    print("="*80)
    print("TEST: TES - Gestión Comercial")
    print("="*80)
    
    # Verificar que el path existe
    if not os.path.exists(REPORT_PATH):
        print(f"[ERROR] El report no existe: {REPORT_PATH}")
        return
    
    print(f"\nPath: {REPORT_PATH}")
    print(f"Basename: {os.path.basename(REPORT_PATH)}")
    print(f"Parent: {os.path.basename(os.path.dirname(REPORT_PATH))}")
    
    # Cargar el report
    print("\n[1] Cargando report...")
    report = clsReport(REPORT_PATH)
    
    print(f"\n[2] Información del report:")
    print(f"  - Formato: {report.report_format}")
    print(f"  - Páginas: {len(report.pages)}")
    print(f"  - Workspace ID inicial: {report.workspace_id}")
    print(f"  - Report ID inicial: {report.report_id}")
    
    # Contar visuals y referencias
    total_visuals = sum(len(page.visuals) for page in report.pages)
    all_columns = report.get_all_columns_used()
    all_measures = report.get_all_measures_used()
    total_columns = sum(len(cols) for cols in all_columns.values())
    total_measures = sum(len(meas) for meas in all_measures.values())
    
    print(f"\n[3] Estadísticas:")
    print(f"  - Total visuals: {total_visuals}")
    print(f"  - Total columnas únicas: {total_columns}")
    print(f"  - Total medidas únicas: {total_measures}")
    
    if total_columns > 0:
        print(f"\n  Columnas encontradas:")
        for table, columns in all_columns.items():
            for col in list(columns)[:5]:
                print(f"    - {table}.{col}")
    
    if total_measures > 0:
        print(f"\n  Medidas encontradas:")
        for table, measures in all_measures.items():
            for meas in list(measures)[:5]:
                print(f"    - {table}.{meas}")
    
    # Guardar en base de datos
    print(f"\n[4] Guardando en base de datos...")
    try:
        conn = duckdb.connect(DB_PATH)
        report.save_to_database(conn)
        
        print(f"\n  Workspace ID después de inferir: {report.workspace_id}")
        print(f"  Report ID después de inferir: {report.report_id}")
        
        # Verificar lo que se guardó
        print(f"\n[5] Verificando datos guardados...")
        
        # Contar registros en las tablas
        tables = ['report_column_used', 'report_measure_used', 'report_visual']
        for table in tables:
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                print(f"  - {table}: {count} registros")
            except:
                print(f"  - {table}: tabla no existe o error")
        
        conn.close()
        print("\n[OK] Completado!")
        
    except Exception as e:
        print(f"\n[ERROR] Error al guardar: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
