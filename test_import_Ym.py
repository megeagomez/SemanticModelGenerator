"""Test para importar workspaces desde Power BI y guardar en DuckDB."""

import sys
import traceback
from datetime import datetime

# Ajusta el path si es necesario para que encuentre el módulo
sys.path.insert(0, r".\Importer\src")

from FabricItemDownloader import FabricItemDownloader
from import_from_powerbi import PowerBIImporter



DEST = r"d:\mcpdata\ysabel"
DB   = "ysabel"

WORKSPACES = [
    "Sales_DF", "Sales_DS", "Informes", "Finance_DF", "Finance_DS",
    "Finance_DS_TEST", "Finance_DF_TEST", "Sales_DF_TEST", "Sales_DS_TEST",
    "Informes_TEST", "Purchase_DF_TEST", "Purchase_DS_TEST", "My workspace",
    "Purchase_DS", "Purchase_DF", "Informes_Finance", "General_DF_TEST",
    "Packaging_DS_TEST", "General_DF", "Packaging_DS", "Executive_DF_TEST",
    "Executive_DS_TEST", "Executive_DF", "Executive_DS", "IT_DF",
    "Marketing_DS_TEST", "Sandbox Commercial", "Informes_Retail_Stores",
    "Informes_Retail_Stores_TEST", "Edicom_DF_TEST", "Edicom_DS_TEST",
    "Edicom_DF", "Edicom_DS", "Stock_DF_TEST", "Stock_DF",
    "Nomarks_DS", "Logistics_DS"
]

def main():
    total    = len(WORKSPACES)
    ok       = []
    errores  = []

    # El downloader se crea una sola vez (reutiliza el token de auth)
    downloader = FabricItemDownloader()

    print(f"\n{'='*60}")
    print(f"  Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Destino: {DEST}  |  DB: {DB}.duckdb")
    print(f"  Total workspaces: {total}")
    print(f"{'='*60}\n")

    for i, workspace in enumerate(WORKSPACES, 1):
        print(f"[{i:02d}/{total}] ▶ {workspace}")
        start = datetime.now()
        try:
            importer = PowerBIImporter(downloader, workspace_name=workspace)
            importer.import_from_powerbi(destination_path=DEST, db_name=DB)
            elapsed = (datetime.now() - start).seconds
            print(f"         ✅ OK  ({elapsed}s)\n")
            ok.append(workspace)
        except Exception as e:
            elapsed = (datetime.now() - start).seconds
            print(f"         ❌ ERROR ({elapsed}s): {e}\n")
            traceback.print_exc()
            errores.append((workspace, str(e)))

    # Resumen final
    print(f"\n{'='*60}")
    print(f"  Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  ✅ Completados: {len(ok)}/{total}")
    if errores:
        print(f"  ❌ Con errores: {len(errores)}/{total}")
        for ws, err in errores:
            print(f"     - {ws}: {err}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()