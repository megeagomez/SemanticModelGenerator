import sys
import duckdb
from models.report_documenter import ReportDocumenter

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Genera documentación HTML de informes Power BI desde DuckDB.")
    parser.add_argument("--db", required=True, help="Ruta a la base DuckDB")
    parser.add_argument("--report", help="Nombre del informe a documentar")
    parser.add_argument("--model", help="Nombre del modelo semántico")
    args = parser.parse_args()

    con = duckdb.connect(args.db, read_only=True)
    doc = ReportDocumenter(con, args.report, semantic_model_name=args.model)
    html = doc.generate_html()
    print(html)
    con.close()
