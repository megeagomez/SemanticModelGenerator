import streamlit as st
from pathlib import Path
import duckdb
import pandas as pd
from models.report_documenter import ReportDocumenter

# ── Page config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="PowerBI Model Generator and Documenter",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
/* General */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #f5f7fa 0%, #e4e9f2 100%);
}
header[data-testid="stHeader"] { background: transparent; }

/* Title bar */
.main-title {
    background: linear-gradient(90deg, #1a237e 0%, #0d47a1 40%, #0277bd 100%);
    color: white;
    padding: 1.2rem 2rem;
    border-radius: 12px;
    margin-bottom: 1.2rem;
    font-family: 'Segoe UI', sans-serif;
    box-shadow: 0 4px 16px rgba(26,35,126,0.18);
}
.main-title h1 { margin: 0; font-size: 1.8rem; font-weight: 700; letter-spacing: 0.3px; }
.main-title p  { margin: 0.3rem 0 0 0; font-size: 0.95rem; opacity: 0.85; }

/* KPI boxes */
.kpi-row { display: flex; gap: 14px; flex-wrap: wrap; margin: 0.8rem 0 1.3rem 0; }
.kpi-box {
    flex: 1; min-width: 130px; max-width: 200px;
    border-radius: 10px; padding: 14px 18px;
    text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    transition: transform 0.15s;
}
.kpi-box:hover { transform: translateY(-2px); box-shadow: 0 4px 14px rgba(0,0,0,0.12); }
.kpi-value { font-size: 1.75rem; font-weight: 700; margin: 0; line-height: 1.2; }
.kpi-label { font-size: 0.78rem; font-weight: 500; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.8; }

/* Tab styling */
button[data-baseweb="tab"] {
    font-weight: 600 !important;
    font-size: 0.88rem !important;
}

/* Section headers */
.section-header {
    font-family: 'Segoe UI', sans-serif;
    font-size: 1.05rem; font-weight: 600; color: #1a237e;
    border-bottom: 2px solid #e3f2fd; padding-bottom: 6px;
    margin: 1.2rem 0 0.7rem 0;
}

/* Report badge */
.report-badge {
    display: inline-block; padding: 4px 12px; border-radius: 16px;
    font-size: 0.82rem; font-weight: 600; margin: 3px 4px;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #fafbff 0%, #e8eaf6 100%);
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] .stTextInput label {
    font-weight: 600; color: #1a237e;
}
</style>
""", unsafe_allow_html=True)

# ── Title ────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-title">
    <h1>📊 PowerBI Model Generator and Documenter</h1>
    <p>Navegador interactivo de modelos semánticos e informes Power BI</p>
</div>
""", unsafe_allow_html=True)

# ── KPI colors ───────────────────────────────────────────────────────
KPI_STYLES = {
    "columns":              {"bg": "#e3f2fd", "color": "#0d47a1", "icon": "🔢", "label": "Columnas"},
    "measures":             {"bg": "#fff3e0", "color": "#e65100", "icon": "📐", "label": "Medidas"},
    "pages":                {"bg": "#e8f5e9", "color": "#2e7d32", "icon": "📄", "label": "Páginas"},
    "tables":               {"bg": "#f3e5f5", "color": "#6a1b9a", "icon": "📋", "label": "Tablas"},
    "relationships":        {"bg": "#fce4ec", "color": "#c62828", "icon": "🔗", "label": "Relaciones"},
    "reports_using_model":  {"bg": "#e0f7fa", "color": "#00695c", "icon": "📑", "label": "Informes"},
}

REPORT_COLORS = [
    "#e3f2fd", "#fff3e0", "#e8f5e9", "#f3e5f5", "#fce4ec",
    "#e0f7fa", "#fff8e1", "#ede7f6", "#e8eaf6", "#fbe9e7",
]
REPORT_TEXT_COLORS = [
    "#0d47a1", "#e65100", "#2e7d32", "#6a1b9a", "#c62828",
    "#00695c", "#f57f17", "#4527a0", "#283593", "#bf360c",
]


def render_kpi_boxes(kpis):
    """Render KPI metrics as colored boxes."""
    html_parts = ['<div class="kpi-row">']
    for key, style in KPI_STYLES.items():
        val = kpis.get(key, 0)
        html_parts.append(
            f'<div class="kpi-box" style="background:{style["bg"]};color:{style["color"]};">'
            f'<p class="kpi-value">{style["icon"]} {val}</p>'
            f'<p class="kpi-label">{style["label"]}</p>'
            f'</div>'
        )
    html_parts.append('</div>')
    st.markdown("".join(html_parts), unsafe_allow_html=True)


def render_page_tab(doc, page):
    """Render the content for a single report page tab."""
    visuals = doc.get_visuals(page)
    svg = doc.generate_svg(page, visuals)
    st.markdown(svg, unsafe_allow_html=True)

    details = doc.get_page_details(page)

    # Columns used
    st.markdown('<div class="section-header">📊 Columnas usadas</div>', unsafe_allow_html=True)
    if details["columns_by_table"]:
        for table_name, cols in details["columns_by_table"].items():
            with st.expander(f"📋 {table_name} ({len(cols)} columnas)", expanded=False):
                for c in cols:
                    st.markdown(f"  - `{c}`")
    else:
        st.info("No se encontraron columnas usadas en esta página.")

    # Measures used
    st.markdown('<div class="section-header">📐 Medidas usadas</div>', unsafe_allow_html=True)
    if details["measures"]:
        for m in details["measures"]:
            if m in details["dax"]:
                with st.expander(f"📐 {m}", expanded=False):
                    st.code(details["dax"][m], language="dax")
            else:
                st.markdown(f"- `{m}`")
    else:
        st.info("No se encontraron medidas usadas en esta página.")

    # M code
    if details["m_code"]:
        st.markdown('<div class="section-header">🔧 Código M (Particiones)</div>', unsafe_allow_html=True)
        for key, expr in details["m_code"].items():
            with st.expander(f"⚙️ {key}", expanded=False):
                st.code(expr, language="m")


def render_model_tab(doc):
    """Render the semantic model details tab."""
    st.markdown('<div class="section-header">📋 Tablas del Modelo</div>', unsafe_allow_html=True)
    tables = doc.get_model_tables()
    if tables:
        df = pd.DataFrame(tables)
        df.columns = ["Tabla", "Oculta"]
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-header">🔢 Columnas del Modelo</div>', unsafe_allow_html=True)
    columns = doc.get_model_columns()
    if columns:
        df = pd.DataFrame(columns)
        df.columns = ["Tabla", "Columna", "Tipo de Dato", "Oculta"]
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-header">📐 Medidas del Modelo</div>', unsafe_allow_html=True)
    measures = doc.get_model_measures()
    if measures:
        for m in measures:
            with st.expander(f"📐 [{m['table_name']}] {m['measure_name']}", expanded=False):
                if m.get("expression"):
                    st.code(m["expression"], language="dax")
                if m.get("format_string"):
                    st.caption(f"Formato: `{m['format_string']}`")
                st.caption(f"Oculta: {'Sí' if m.get('is_hidden') else 'No'}")

    st.markdown('<div class="section-header">🔗 Relaciones</div>', unsafe_allow_html=True)
    rels = doc.get_model_relationships()
    if rels:
        df = pd.DataFrame(rels)
        df.columns = ["Nombre", "Desde Tabla", "Desde Columna", "Hacia Tabla",
                       "Hacia Columna", "Cardinalidad", "Filtro Cruzado", "Activa"]
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-header">⚙️ Particiones (código M)</div>', unsafe_allow_html=True)
    partitions = doc.get_model_partitions()
    if partitions:
        for p in partitions:
            label = f"⚙️ {p['table_name']}.{p['partition_name']} ({p.get('source_type', '')})"
            with st.expander(label, expanded=False):
                if p.get("source_expression"):
                    st.code(p["source_expression"], language="m")
                st.caption(f"Modo: {p.get('mode', 'N/A')}")


def render_unused_tab(doc):
    """Render the full unused objects inventory tab."""
    summary = doc.get_unused_summary()
    n_cols = summary["total_unused_columns"]
    n_meas = summary["total_unused_measures"]
    n_tables = summary["total_unused_tables"]
    total = n_cols + n_meas + n_tables

    if total == 0:
        st.success("✅ Todos los objetos del modelo están siendo usados en al menos un informe.")
        return

    # Overview KPI row
    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-box" style="background:#fff3e0;color:#e65100;">
            <p class="kpi-value">⚠️ {n_tables}</p>
            <p class="kpi-label">Tablas sin usar</p>
        </div>
        <div class="kpi-box" style="background:#fce4ec;color:#c62828;">
            <p class="kpi-value">⚠️ {n_cols}</p>
            <p class="kpi-label">Columnas sin usar</p>
        </div>
        <div class="kpi-box" style="background:#f3e5f5;color:#6a1b9a;">
            <p class="kpi-value">⚠️ {n_meas}</p>
            <p class="kpi-label">Medidas sin usar</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Unused tables ────────────────────────────────────────────
    if summary["unused_tables"]:
        st.markdown('<div class="section-header">📋 Tablas sin usar</div>', unsafe_allow_html=True)
        for t in summary["unused_tables"]:
            st.markdown(f"- `{t['table_name']}`" + (" _(oculta)_" if t.get("is_hidden") else ""))

    # ── Unused columns by table ──────────────────────────────────
    if summary["columns_by_table"]:
        st.markdown('<div class="section-header">🔢 Columnas sin usar por tabla</div>', unsafe_allow_html=True)
        for table_name in sorted(summary["columns_by_table"].keys()):
            cols = summary["columns_by_table"][table_name]
            with st.expander(f"📋 {table_name} ({len(cols)} columnas sin usar)", expanded=False):
                df = pd.DataFrame(cols)
                df = df[["column_name", "data_type", "is_hidden"]]
                df.columns = ["Columna", "Tipo", "Oculta"]
                st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Unused measures by table ─────────────────────────────────
    if summary["measures_by_table"]:
        st.markdown('<div class="section-header">📐 Medidas sin usar por tabla</div>', unsafe_allow_html=True)
        for table_name in sorted(summary["measures_by_table"].keys()):
            measures = summary["measures_by_table"][table_name]
            with st.expander(f"📐 {table_name} ({len(measures)} medidas sin usar)", expanded=False):
                for m in measures:
                    st.markdown(f"**{m['measure_name']}**")
                    if m.get("expression"):
                        st.code(m["expression"], language="dax")


def render_minimal_model_tab(doc, con):
    """Render the minimal model generation tab."""
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    if not doc.semantic_model_id:
        st.warning("No se encontró un modelo semántico vinculado.")
        return

    st.markdown('<div class="section-header">⚡ Generar Modelo Mínimo</div>', unsafe_allow_html=True)
    st.markdown(
        "Genera un nuevo modelo semántico con **solo las tablas, columnas y medidas** "
        "utilizadas por los informes vinculados. Las columnas y medidas sin usar se eliminan, "
        "y el código M se ajusta con `Table.RemoveColumns`."
    )

    # Show what would be included
    summary = doc.get_unused_summary()
    kpis = doc.get_kpis()
    total_cols = kpis.get("columns", 0)
    total_meas = kpis.get("measures", 0)
    total_tables = kpis.get("tables", 0)
    used_cols = total_cols - summary["total_unused_columns"]
    used_meas = total_meas - summary["total_unused_measures"]
    used_tables = total_tables - summary["total_unused_tables"]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tablas", f"{used_tables} / {total_tables}",
                   delta=f"-{summary['total_unused_tables']}" if summary['total_unused_tables'] else None,
                   delta_color="normal")
    with col2:
        st.metric("Columnas", f"{used_cols} / {total_cols}",
                   delta=f"-{summary['total_unused_columns']}" if summary['total_unused_columns'] else None,
                   delta_color="normal")
    with col3:
        st.metric("Medidas", f"{used_meas} / {total_meas}",
                   delta=f"-{summary['total_unused_measures']}" if summary['total_unused_measures'] else None,
                   delta_color="normal")

    st.markdown("---")

    # Get model source path info
    sm_row = con.execute(
        "SELECT sm.name, w.displayName FROM semantic_model sm "
        "LEFT JOIN workspaces w ON sm.workspace_id = w.id "
        "WHERE sm.id = ?", [doc.semantic_model_id]
    ).fetchone()
    sm_name = sm_row[0] if sm_row else doc._sm_name
    workspace_name = sm_row[1] if sm_row else None

    # DB path from session state
    db_path = st.session_state.get("_current_db_path", "")
    base_dir_val = st.session_state.get("_current_base_dir", "")

    # Source model path
    if base_dir_val and workspace_name:
        source_model_path = str(Path(base_dir_val) / workspace_name / sm_name)
        st.info(f"📂 Modelo fuente: `{source_model_path}`")
    else:
        source_model_path = ""
        st.warning("No se puede determinar la ruta del modelo fuente. "
                    "Asegúrate de que la base de datos tenga la estructura "
                    "`carpeta/workspace/modelo.SemanticModel`.")

    # Output path
    default_subset_name = sm_name.replace(".SemanticModel", "") + "_minimal.SemanticModel"
    subset_name = st.text_input(
        "📝 Nombre del modelo mínimo",
        value=default_subset_name,
        help="Nombre del nuevo modelo semántico"
    ) or default_subset_name

    if source_model_path:
        output_dir = str(Path(source_model_path).parent / subset_name)
        st.caption(f"📁 Se guardará en: `{output_dir}`")

    # Generate button
    if st.button("⚡ Generar Modelo Mínimo", type="primary", use_container_width=True):
        if not source_model_path:
            st.error("No se puede generar: falta la ruta del modelo fuente.")
            return
        if not Path(source_model_path).exists():
            st.error(f"No se encontró el modelo fuente en: `{source_model_path}`")
            return

        with st.spinner("Generando modelo mínimo..."):
            try:
                from models.semantic_model import SemanticModel

                model = SemanticModel(source_model_path)
                model.load_from_directory(Path(source_model_path))

                subset = model.create_subset_model_from_db(
                    db_path=db_path,
                    subset_name=subset_name,
                    semantic_model_id=doc.semantic_model_id,
                )

                target_path = Path(source_model_path).parent / subset_name
                subset.save_to_directory(target_path)

                st.success(
                    f"✅ Modelo mínimo generado: **{subset_name}**\n\n"
                    f"- Tablas: {len(subset.tables)}\n"
                    f"- Relaciones: {len(subset.relationships)}\n"
                    f"- Guardado en: `{target_path}`"
                )

                # Show details
                with st.expander("📋 Detalle de tablas incluidas", expanded=True):
                    table_data = []
                    for t in sorted(subset.tables, key=lambda t: t.name):
                        table_data.append({
                            "Tabla": t.name,
                            "Columnas": len(t.columns),
                            "Medidas": len(t.measures),
                        })
                    if table_data:
                        st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

            except Exception as e:
                st.error(f"Error al generar el modelo: {e}")
                import traceback
                st.code(traceback.format_exc())


def render_report(doc, report_name, badge_color=None, badge_text_color=None):
    """Render a full report view with dynamic tabs."""
    kpis = doc.get_kpis()
    render_kpi_boxes(kpis)

    if not doc.pages:
        st.info("Este informe no tiene páginas.")
        return

    # Top-level tabs: always visible
    top_tabs = st.tabs([
        "📄 Páginas del Informe",
        "🗃️ Modelo Semántico",
        "🔍 Objetos sin usar",
        "⚡ Modelo Mínimo",
    ])

    # ── Pages tab (nested page tabs inside) ──────────────────────
    with top_tabs[0]:
        page_labels = []
        for p in doc.pages:
            label = p.get("display_name") or p.get("name") or "Page"
            page_labels.append(f"📄 {label}")
        page_tabs = st.tabs(page_labels)
        for i, page in enumerate(doc.pages):
            with page_tabs[i]:
                render_page_tab(doc, page)

    # ── Semantic model tab ───────────────────────────────────────
    with top_tabs[1]:
        render_model_tab(doc)

    # ── Unused objects tab ───────────────────────────────────────
    with top_tabs[2]:
        render_unused_tab(doc)

    # ── Minimal model tab ────────────────────────────────────────
    with top_tabs[3]:
        render_minimal_model_tab(doc, con)


# ══════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    base_dir = st.text_input(
        "📂 Ruta carpeta DuckDB",
        value=r"D:\Modelos",
        help="Carpeta que contiene archivos .duckdb",
    )

    if base_dir:
        DUCKDB_DIR = Path(base_dir)
        duckdb_files = sorted([str(p) for p in DUCKDB_DIR.glob("*.duckdb")])

        if not duckdb_files:
            st.warning("No se encontraron archivos .duckdb en la ruta indicada.")
            st.stop()

        ws = st.selectbox(
            "🗄️ Base de datos",
            duckdb_files,
            format_func=lambda x: Path(x).stem,
        )

        # Workspace filter with counts and sorting
        workspace_options = []
        workspace_map = {}
        if ws:
            try:
                con_tmp = duckdb.connect(ws, read_only=True)
                rows = con_tmp.execute("SELECT id, displayName FROM workspaces ORDER BY displayName").fetchall()
                # Get counts for each workspace
                counts = {}
                for r in rows:
                    wid = r[0]
                    n_reports = con_tmp.execute("SELECT COUNT(*) FROM report WHERE workspace_id = ?", [wid]).fetchone()[0]
                    n_models = con_tmp.execute("SELECT COUNT(*) FROM semantic_model WHERE workspace_id = ?", [wid]).fetchone()[0]
                    counts[wid] = (n_reports, n_models)
                con_tmp.close()
                # Sort: non-empty first, then separator, then empty
                non_empty = []
                empty = []
                for r in rows:
                    wid = r[0]
                    n_reports, n_models = counts[wid]
                    display = f"{r[1]} (reports: {n_reports}, models: {n_models})"
                    if n_reports > 0 or n_models > 0:
                        non_empty.append((display, wid))
                    else:
                        empty.append((display, wid))
                workspace_options = [d for d, w in non_empty]
                workspace_map = {d: w for d, w in non_empty}
                if empty:
                    workspace_options.append("---")
                    for d, w in empty:
                        workspace_options.append(d)
                        workspace_map[d] = w
            except Exception:
                workspace_options = []
                workspace_map = {}

        selected_workspace = None
        if workspace_options:
            # Remove separator from selectable options
            selectable_options = [opt for opt in workspace_options if opt != "---"]
            selected_workspace_display = st.selectbox(
                "🏢 Workspace (filtro)", selectable_options, index=0)
            selected_workspace = workspace_map.get(selected_workspace_display)
        else:
            selected_workspace = None

        st.markdown("---")
        search_mode = st.radio(
            "🔍 Buscar por",
            ["📄 Informe", "🗃️ Modelo"],
            horizontal=True,
            help="Elige si quieres explorar desde un informe o desde un modelo semántico",
        )
    else:
        st.warning("Introduce la ruta de la carpeta con bases DuckDB.")
        st.stop()

# ══════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ══════════════════════════════════════════════════════════════════════
if base_dir and ws:
    # Store in session state for use by the minimal model tab
    st.session_state["_current_db_path"] = ws
    st.session_state["_current_base_dir"] = base_dir
    con = duckdb.connect(ws, read_only=True)

    try:
        if 'selected_workspace' in locals() and selected_workspace:
            all_reports = con.execute(
                "SELECT name FROM report WHERE workspace_id = ? ORDER BY name", [selected_workspace]
            ).fetchall()
            all_models = con.execute(
                "SELECT name FROM semantic_model WHERE workspace_id = ? ORDER BY name", [selected_workspace]
            ).fetchall()
        else:
            all_reports = con.execute("SELECT name FROM report ORDER BY name").fetchall()
            all_models = con.execute("SELECT name FROM semantic_model ORDER BY name").fetchall()
        report_names = [r[0] for r in all_reports]
        model_names = [m[0] for m in all_models]
    except Exception as e:
        st.error(f"Error al leer la base de datos: {e}")
        con.close()
        st.stop()

    # ── Search by Report ─────────────────────────────────────────────
    if search_mode == "📄 Informe":
        with st.sidebar:
            selected_report = st.selectbox("📄 Informe", report_names)

        if selected_report:
            sm_name = ReportDocumenter.get_model_for_report(con, selected_report)
            if sm_name:
                with st.sidebar:
                    st.info(f"🗃️ Modelo: **{sm_name}**")

            doc = ReportDocumenter(con, selected_report, semantic_model_name=sm_name)
            st.markdown(
                f'<div style="background:#e8eaf6;padding:10px 18px;border-radius:8px;'
                f'margin-bottom:10px;"><b>📄 Informe:</b> {selected_report}'
                + (f' &nbsp;→&nbsp; <b>🗃️ Modelo:</b> {sm_name}' if sm_name else '')
                + '</div>',
                unsafe_allow_html=True,
            )
            render_report(doc, selected_report)
        else:
            st.info("Selecciona un informe en el panel lateral.")

    # ── Search by Model ──────────────────────────────────────────────
    else:
        with st.sidebar:
            selected_model = st.selectbox("🗃️ Modelo Semántico", model_names)

        if selected_model:
            linked_reports = ReportDocumenter.get_reports_for_model(con, selected_model)

            # Show model info header
            st.markdown(
                f'<div style="background:#f3e5f5;padding:10px 18px;border-radius:8px;'
                f'margin-bottom:10px;"><b>🗃️ Modelo:</b> {selected_model}'
                f' &nbsp;|&nbsp; <b>{len(linked_reports)}</b> informes vinculados</div>',
                unsafe_allow_html=True,
            )

            if not linked_reports:
                st.warning("No se encontraron informes vinculados a este modelo.")
                doc = ReportDocumenter(con, "__no_report__", semantic_model_name=selected_model)
                tab_model, tab_unused, tab_minimal = st.tabs(
                    ["🗃️ Modelo Semántico", "🔍 Objetos sin usar", "⚡ Modelo Mínimo"])
                with tab_model:
                    render_model_tab(doc)
                with tab_unused:
                    render_unused_tab(doc)
                with tab_minimal:
                    render_minimal_model_tab(doc, con)
            else:
                # Show badges for linked reports
                badges_html = '<div style="margin-bottom:12px;">'
                for idx, rname in enumerate(linked_reports):
                    ci = idx % len(REPORT_COLORS)
                    badges_html += (
                        f'<span class="report-badge" style="background:{REPORT_COLORS[ci]};'
                        f'color:{REPORT_TEXT_COLORS[ci]};">📄 {rname}</span>'
                    )
                badges_html += '</div>'
                st.markdown(badges_html, unsafe_allow_html=True)

                # Let user pick which report to explore
                with st.sidebar:
                    st.markdown("---")
                    active_report = st.selectbox(
                        "📄 Selecciona un informe",
                        linked_reports,
                        help="Informes vinculados al modelo seleccionado",
                    )

                if active_report:
                    ri = linked_reports.index(active_report) % len(REPORT_COLORS)
                    st.markdown(
                        f'<div style="background:{REPORT_COLORS[ri]};color:{REPORT_TEXT_COLORS[ri]};'
                        f'padding:8px 18px;border-radius:8px;margin-bottom:8px;font-weight:600;">'
                        f'📄 {active_report}</div>',
                        unsafe_allow_html=True,
                    )
                    doc = ReportDocumenter(con, active_report, semantic_model_name=selected_model)
                    render_report(doc, active_report,
                                  badge_color=REPORT_COLORS[ri],
                                  badge_text_color=REPORT_TEXT_COLORS[ri])
        else:
            st.info("Selecciona un modelo en el panel lateral.")

    con.close()
