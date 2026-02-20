"""
Test para procesar todos los reports de Toyota y guardarlos en la base de datos.
Procesa reports en modo legacy y extrae columnas, medidas y filtros usados.
"""

import os
from datetime import datetime

import duckdb

from models.report import clsReport


TOYOTA_BASE_PATH = r"D:\mcpdata\toyota"
TOYOTA_DB_PATH = r"D:\mcpdata\toyota\toyota.duckdb"


def find_all_reports(base_path: str) -> list:
    """Busca recursivamente todos los .Report folders en la ruta base."""
    report_folders = []
    for root, dirs, files in os.walk(base_path):
        for dir_name in dirs:
            if dir_name.endswith(".Report"):
                report_folders.append(os.path.join(root, dir_name))
    return report_folders


def process_report_simple(report_path: str, conn) -> dict:
    """Procesa un report y lo guarda en la base de datos. Retorna estadisticas."""
    stats = {
        "path": report_path,
        "name": os.path.basename(report_path),
        "success": False,
        "format": None,
        "pages": 0,
        "visuals": 0,
        "columns": 0,
        "measures": 0,
        "filters": 0,
        "error": None,
    }

    try:
        report = clsReport(report_path)
        stats["format"] = report.report_format
        stats["pages"] = len(report.pages)
        for page in report.pages:
            stats["visuals"] += len(page.visuals)

        all_columns = report.get_all_columns_used()
        all_measures = report.get_all_measures_used()
        stats["columns"] = sum(len(cols) for cols in all_columns.values())
        stats["measures"] = sum(len(meas) for meas in all_measures.values())
        stats["filters"] = len(report.filters)

        report.save_to_database(conn)
        stats["success"] = True
    except Exception as e:
        stats["error"] = str(e)

    return stats


def main():
    print("=" * 80)
    print("CARGA MASIVA: Reports Toyota a Base de Datos")
    print("=" * 80)
    print(f"Base Path: {TOYOTA_BASE_PATH}")
    print(f"Database:  {TOYOTA_DB_PATH}")
    print(f"Inicio:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    if not os.path.exists(TOYOTA_BASE_PATH):
        print(f"[ERROR] La ruta no existe: {TOYOTA_BASE_PATH}")
        return

    print("\n[1/4] Buscando reports...")
    report_folders = find_all_reports(TOYOTA_BASE_PATH)
    print(f"      Encontrados {len(report_folders)} reports")
    if not report_folders:
        print("[ERROR] No se encontraron reports (.Report folders)")
        return

    print("\n[2/4] Conectando a la base de datos...")
    try:
        conn = duckdb.connect(TOYOTA_DB_PATH)
        print(f"      Conectado a: {TOYOTA_DB_PATH}")
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a la base de datos: {e}")
        return

    print(f"\n[3/4] Procesando {len(report_folders)} reports...")
    print("-" * 80)

    all_stats = []
    successful = 0
    failed = 0

    for idx, report_path in enumerate(report_folders, 1):
        print(f"\n  [{idx}/{len(report_folders)}] {os.path.basename(report_path)}")
        stats = process_report_simple(report_path, conn)
        all_stats.append(stats)

        if stats["success"]:
            successful += 1
            print(
                f"  [OK] {stats['name']} | Formato: {stats['format']} | "
                f"Paginas: {stats['pages']} | Visuals: {stats['visuals']} | "
                f"Columnas: {stats['columns']} | Medidas: {stats['measures']}"
            )
        else:
            failed += 1
            print(f"  [ERROR] {stats['name']}: {stats['error']}")

    conn.close()

    print("\n" + "=" * 80)
    print("[4/4] RESUMEN FINAL")
    print("=" * 80)
    print(f"Total reports procesados: {len(report_folders)}")
    print(f"  Exitosos: {successful}")
    print(f"  Fallidos:  {failed}")

    if successful > 0:
        total_pages = sum(s["pages"] for s in all_stats if s["success"])
        total_visuals = sum(s["visuals"] for s in all_stats if s["success"])
        total_columns = sum(s["columns"] for s in all_stats if s["success"])
        total_measures = sum(s["measures"] for s in all_stats if s["success"])

        print("\nEstadisticas acumuladas:")
        print(f"  Total paginas:  {total_pages}")
        print(f"  Total visuals:  {total_visuals}")
        print(f"  Total columnas unicas: {total_columns}")
        print(f"  Total medidas unicas:  {total_measures}")

    print(f"\nFin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print(f"\nBase de datos actualizada: {TOYOTA_DB_PATH}")


if __name__ == "__main__":
    main()