import streamlit as st
from pathlib import Path
import duckdb
from models.report_documenter import ReportDocumenter

st.set_page_config(page_title="DuckDB Power BI Browser", layout="wide")
st.title("DuckDB Power BI Browser")

base_dir = st.text_input("Ruta de la carpeta con bases DuckDB", value="data")

if base_dir:
    DUCKDB_DIR = Path(base_dir)
    def list_workspaces():
        return [str(p) for p in DUCKDB_DIR.glob("*.duckdb")]

    def list_reports(db_path):
        con = duckdb.connect(db_path, read_only=True)
        rows = con.execute("SELECT id, name FROM report").fetchall()
        con.close()
        return [(f"{row[1]} ({row[0]})", row[1]) for row in rows]

    def list_models(db_path):
        con = duckdb.connect(db_path, read_only=True)
        rows = con.execute("SELECT id, name FROM semantic_model").fetchall()
        con.close()
        return [(f"{row[1]} ({row[0]})", row[1]) for row in rows]

    workspaces = list_workspaces()
    ws = st.selectbox("Workspace (DuckDB)", workspaces)

    if ws:
        reports = list_reports(ws)
        models = list_models(ws)
        col1, col2 = st.columns(2)
        with col1:
            report_display = st.selectbox("Report", [r[0] for r in reports])
            report_name = next((r[1] for r in reports if r[0] == report_display), None)
        with col2:
            model_display = st.selectbox("Semantic Model", [m[0] for m in models])
            model_name = next((m[1] for m in models if m[0] == model_display), None)

        if report_name:
            con = duckdb.connect(ws, read_only=True)
            doc = ReportDocumenter(con, report_name, semantic_model_name=model_name)
            kpis = doc.get_kpis()
            st.markdown(f"**Columnas:** {kpis['columns']} | **Métricas:** {kpis['measures']} | **Páginas:** {kpis['pages']} | **Informes que usan el modelo:** {kpis['reports_using_model']}")
            for page in doc.pages:
                st.header(f"Página: {page.get('display_name') or page.get('name')}")
                visuals = doc.get_visuals(page)
                svg = doc.generate_svg(page, visuals)
                st.markdown(svg, unsafe_allow_html=True)
                details = doc.get_page_details(page)
                st.subheader("Columnas usadas")
                for table, cols in details["columns_by_table"].items():
                    st.write(f"{table}: {', '.join(cols)}")
                st.subheader("Métricas usadas")
                for m in details["measures"]:
                    st.write(f"{m}")
                    if m in details["dax"]:
                        st.code(details["dax"][m], language="dax")
                st.subheader("Código M de particiones")
                for mcode in details["m_code"]:
                    st.code(mcode, language="m")
            con.close()
