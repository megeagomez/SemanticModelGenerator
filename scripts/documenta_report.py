#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
documenta_report.py
Genera documentación HTML de informes Power BI leyendo toda la información
desde una base de datos DuckDB (previamente persistida).

Uso:
    # Un informe concreto:
    python scripts/documenta_report.py --db data/powerbi.duckdb --report "FullAdventureWorks"

    # Todos los informes de la base de datos:
    python scripts/documenta_report.py --db data/powerbi.duckdb --all

    # Listar informes disponibles:
    python scripts/documenta_report.py --db data/powerbi.duckdb --list

    # Guardar en carpeta:
    python scripts/documenta_report.py --db data/powerbi.duckdb --all --output-dir docs/
"""

import sys
import os
import math
import random
import argparse
import html as html_mod
from datetime import datetime
from collections import defaultdict

try:
    import duckdb
except ImportError:
    print("ERROR: duckdb no está instalado. Ejecuta: pip install duckdb", file=sys.stderr)
    sys.exit(1)


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def _esc(text):
    """Escapa HTML."""
    if text is None:
        return ""
    return html_mod.escape(str(text))


# ──────────────────────────────────────────────────────────────────────
# Data access layer – todas las queries a DuckDB
# ──────────────────────────────────────────────────────────────────────

def _get_report(con, report_name: str) -> dict:
    """Obtiene los datos de un informe por nombre."""
    row = con.execute(
        "SELECT id, name, report_id, workspace_id, semantic_model_reference, "
        "schema, active_page_name FROM report WHERE name = ?",
        [report_name]
    ).fetchone()
    if not row:
        return None
    return dict(zip(
        ["id", "name", "report_id", "workspace_id", "semantic_model_reference",
         "schema", "active_page_name"], row
    ))


def _get_all_report_names(con) -> list:
    """Devuelve todos los nombres de informe en la BD."""
    return [r[0] for r in con.execute("SELECT name FROM report ORDER BY name").fetchall()]


def _get_pages(con, report_name: str) -> list:
    """Obtiene las páginas de un informe."""
    cols = ["id", "name", "display_name", "height", "width", "display_option", "is_visible"]
    # Verificar si existe la columna is_visible
    page_cols = [c[0] for c in con.execute("DESCRIBE report_page").fetchall()]
    if "is_visible" not in page_cols:
        cols.remove("is_visible")
    rows = con.execute(
        f"SELECT {', '.join(cols)} FROM report_page WHERE report_name = ? ORDER BY id",
        [report_name]
    ).fetchall()
    pages = []
    for row in rows:
        d = dict(zip(cols, row))
        if "is_visible" not in d:
            d["is_visible"] = True
        pages.append(d)
    return pages


def _get_visuals(con, report_id: int, page_name: str) -> list:
    """Obtiene los visuales de una página."""
    rows = con.execute(
        "SELECT name, visual_type, position_x, position_y, position_width, "
        "position_height, text_content, navigation_target "
        "FROM report_visual WHERE report_id = ? AND page_name = ? ORDER BY id",
        [report_id, page_name]
    ).fetchall()
    cols = ["name", "visual_type", "x", "y", "width", "height", "text_content", "navigation_target"]
    return [dict(zip(cols, r)) for r in rows]


def _get_columns_by_page(con, report_id: int, page_name: str) -> dict:
    """Obtiene columnas usadas en una página agrupadas por tabla."""
    rows = con.execute(
        "SELECT DISTINCT table_name, column_name FROM report_column_used "
        "WHERE report_id = ? AND page_name = ?",
        [report_id, page_name]
    ).fetchall()
    result = defaultdict(set)
    for table, col in rows:
        result[table].add(col)
    return dict(result)


def _get_measures_by_page(con, report_id: int, page_name: str) -> dict:
    """Obtiene medidas usadas en una página agrupadas por tabla."""
    rows = con.execute(
        "SELECT DISTINCT table_name, measure_name FROM report_measure_used "
        "WHERE report_id = ? AND page_name = ?",
        [report_id, page_name]
    ).fetchall()
    result = defaultdict(set)
    for table, measure in rows:
        result[table].add(measure)
    return dict(result)


def _get_all_columns(con, report_id: int) -> dict:
    """Obtiene todas las columnas del informe agrupadas por tabla."""
    rows = con.execute(
        "SELECT DISTINCT table_name, column_name FROM report_column_used WHERE report_id = ?",
        [report_id]
    ).fetchall()
    result = defaultdict(set)
    for table, col in rows:
        result[table].add(col)
    return dict(result)


def _get_all_measures(con, report_id: int) -> dict:
    """Obtiene todas las medidas del informe agrupadas por tabla."""
    rows = con.execute(
        "SELECT DISTINCT table_name, measure_name FROM report_measure_used WHERE report_id = ?",
        [report_id]
    ).fetchall()
    result = defaultdict(set)
    for table, measure in rows:
        result[table].add(measure)
    return dict(result)


def _get_kpis(con, report_id: int, report_name: str) -> dict:
    """Calcula los KPIs del informe."""
    num_pages = con.execute(
        "SELECT COUNT(*) FROM report_page WHERE report_name = ?", [report_name]
    ).fetchone()[0]
    num_visuals = con.execute(
        "SELECT COUNT(*) FROM report_visual WHERE report_id = ?", [report_id]
    ).fetchone()[0]
    all_tables = con.execute(
        "SELECT COUNT(DISTINCT table_name) FROM ("
        "  SELECT table_name FROM report_column_used WHERE report_id = ? "
        "  UNION "
        "  SELECT table_name FROM report_measure_used WHERE report_id = ?"
        ")", [report_id, report_id]
    ).fetchone()[0]
    num_columns = con.execute(
        "SELECT COUNT(DISTINCT table_name || '.' || column_name) FROM report_column_used WHERE report_id = ?",
        [report_id]
    ).fetchone()[0]
    num_measures = con.execute(
        "SELECT COUNT(DISTINCT table_name || '.' || measure_name) FROM report_measure_used WHERE report_id = ?",
        [report_id]
    ).fetchone()[0]
    return {
        "pages": num_pages,
        "visuals": num_visuals,
        "tables": all_tables,
        "columns": num_columns,
        "measures": num_measures,
    }


def _find_semantic_model(con, report: dict) -> dict:
    """Encuentra el modelo semántico asociado al informe.
    Estrategias:
      1. Por semantic_model_reference
      2. Por nombre: sm.name = report.name + '.SemanticModel'
      3. Por semantic_model_id: 'local_' + report.name
    """
    sm_ref = report.get("semantic_model_reference")
    sm = None

    if sm_ref:
        row = con.execute(
            "SELECT id, name, semantic_model_id FROM semantic_model WHERE semantic_model_id = ?",
            [sm_ref]
        ).fetchone()
        if row:
            sm = {"id": row[0], "name": row[1], "semantic_model_id": row[2]}

    if not sm:
        sm_name = report["name"] + ".SemanticModel"
        row = con.execute(
            "SELECT id, name, semantic_model_id FROM semantic_model WHERE name = ?",
            [sm_name]
        ).fetchone()
        if row:
            sm = {"id": row[0], "name": row[1], "semantic_model_id": row[2]}

    if not sm:
        local_id = "local_" + report["name"]
        row = con.execute(
            "SELECT id, name, semantic_model_id FROM semantic_model WHERE semantic_model_id = ?",
            [local_id]
        ).fetchone()
        if row:
            sm = {"id": row[0], "name": row[1], "semantic_model_id": row[2]}

    return sm


def _find_reports_sharing_model(con, report: dict, sm: dict) -> list:
    """Busca otros informes que comparten el mismo modelo semántico."""
    results = []
    sm_ref = report.get("semantic_model_reference")
    report_id = report["id"]

    if sm_ref:
        rows = con.execute(
            "SELECT name FROM report WHERE semantic_model_reference = ? AND id != ? ORDER BY name",
            [sm_ref, report_id]
        ).fetchall()
        results = [r[0] for r in rows]

    if not results and sm:
        rows = con.execute(
            "SELECT r.name FROM report r "
            "JOIN semantic_model s ON (s.name = r.name || '.SemanticModel' "
            "  OR s.semantic_model_id = 'local_' || r.name) "
            "WHERE s.id = ? AND r.id != ? ORDER BY r.name",
            [sm["id"], report_id]
        ).fetchall()
        results = [r[0] for r in rows]

    return results


def _get_measure_dax_lookup(con, sm_id: int) -> dict:
    """Construye un diccionario {Tabla.Medida: expression_dax} desde el SM."""
    rows = con.execute(
        "SELECT table_name, measure_name, expression FROM semantic_model_measure WHERE semantic_model_id = ?",
        [sm_id]
    ).fetchall()
    lookup = {}
    for table, measure, expr in rows:
        lookup[f"{table}.{measure}"] = _clean_dax_expression(expr)
    return lookup


def _clean_dax_expression(expr: str) -> str:
    """Limpia la expresión DAX eliminando metadata embebida."""
    if not expr:
        return ""
    lines = expr.split("\n")
    dax_lines = []
    for line in lines:
        stripped = line.strip()
        if any(stripped.startswith(tag) for tag in [
            "displayFolder:", "lineageTag:", "formatString:", "isHidden",
            "annotation ", "changedProperty"
        ]):
            continue
        dax_lines.append(line)
    return "\n".join(dax_lines).rstrip()


def _get_partition_m_code(con, sm_id: int, table_name: str) -> str:
    """Obtiene el código M (source_expression) de una tabla."""
    row = con.execute(
        "SELECT source_expression FROM semantic_model_partitions "
        "WHERE semantic_model_id = ? AND table_name = ? AND source_expression IS NOT NULL "
        "AND source_expression != '' LIMIT 1",
        [sm_id, table_name]
    ).fetchone()
    return row[0] if row else None


# ──────────────────────────────────────────────────────────────────────
# SVG mockup generator (desde datos de la BD)
# ──────────────────────────────────────────────────────────────────────

def _generate_svg_from_db(page: dict, visuals: list) -> str:
    """Genera un SVG mockup de la página usando datos de report_visual."""
    width = page.get("width") or 1280
    height = page.get("height") or 720

    svg_parts = [
        f"<svg width='{width}' height='{height}' xmlns='http://www.w3.org/2000/svg'>",
        f"<rect width='{width}' height='{height}' fill='#f9f9f9' stroke='#ccc'/>",
        f"<text x='10' y='20' font-family='Segoe UI' font-size='16' fill='#333'>"
        f"Página: {_esc(page.get('display_name') or page.get('name', ''))}</text>"
    ]

    for v in visuals:
        x = v.get("x") or 0
        y = v.get("y") or 0
        w = v.get("width") or 200
        h = v.get("height") or 160
        tipo = (v.get("visual_type") or "unknown").lower()
        label = v.get("text_content") or v.get("visual_type") or v.get("name") or "Visual"
        svg_parts.append(_draw_visual(tipo, x, y, w, h, label))

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def _draw_visual(tipo: str, x, y, w, h, label) -> str:
    """Dibuja un visual individual en SVG según su tipo."""
    tipo_lower = tipo.lower() if tipo else "unknown"

    draw_map = {
        "slicer": _draw_slicer,
        "donutchart": _draw_donutchart,
        "clusteredcolumnchart": _draw_clusteredcolumnchart,
        "columnchart": _draw_columnchart,
        "funnel": _draw_funnel,
        "piechart": _draw_piechart,
        "table": _draw_table,
        "kpi": _draw_kpi,
        "lineclusteredcolumncombochart": _draw_line_combo,
        "textbox": _draw_textbox,
        "ribbonchart": _draw_ribbonchart,
        "card": _draw_card,
        "areachart": _draw_areachart,
        "bcicalendar": _draw_bci_calendar,
        "linechart": _draw_linechart,
        "pivottable": _draw_table,
        "treemap": _draw_treemap,
        "map": _draw_map_visual,
        "filledmap": _draw_map_visual,
        "waterfallchart": _draw_waterfall,
        "gauge": _draw_gauge,
        "multirowcard": _draw_card,
        "scatterchart": _draw_scatter,
        "decompositiontreevisual": _draw_tree,
        "image": _draw_image,
        "shape": _draw_shape,
        "actionbutton": _draw_button,
        "clusteredbarchart": _draw_clusteredcolumnchart,
        "stackedbarchart": _draw_columnchart,
        "stackedcolumnchart": _draw_columnchart,
        "hundredpercentstackedbarchart": _draw_columnchart,
        "hundredpercentstackedcolumnchart": _draw_columnchart,
        "matrixvisual": _draw_table,
        "matrix": _draw_table,
    }

    draw_fn = draw_map.get(tipo_lower)
    if draw_fn:
        return draw_fn(x, y, w, h, _esc(label))
    else:
        return _draw_default(x, y, w, h, _esc(label), tipo_lower)


def _draw_slicer(x, y, w, h, label):
    return (f"<g transform='translate({x},{y})'>"
            f"<rect width='{w}' height='{h}' rx='8' ry='8' fill='#f4f4f4' stroke='#ccc'/>"
            f"<text x='10' y='20' font-family='Segoe UI' font-size='14' fill='#333'>{label}</text>"
            f"<rect x='10' y='30' width='{w-20}' height='30' rx='4' ry='4' fill='#fff' stroke='#aaa'/>"
            f"<text x='15' y='50' font-family='Segoe UI' font-size='13' fill='#666'>▼</text>"
            f"</g>")


def _draw_clusteredcolumnchart(x, y, w, h, label):
    margin = 20
    bars = ""
    for i in range(4):
        for j in range(3):
            bw = max(6, min(10, w/20))
            bh = random.randint(20, max(21, int(h*0.6)))
            bx = margin + i * (w-2*margin)/4 + j * (bw+2)
            by = h - margin - bh
            colors = ["rgb(0,100,150)", "rgb(50,130,130)", "rgb(100,160,110)"]
            bars += f"<rect x='{bx}' y='{by}' width='{bw}' height='{bh}' fill='{colors[j]}'/>"
    return (f"<g transform='translate({x},{y})'>"
            f"<rect width='{w}' height='{h}' fill='#fff' stroke='#ccc' rx='6' ry='6'/>"
            f"<text x='10' y='18' font-family='Segoe UI' font-size='12' fill='#333'>{label}</text>"
            f"<line x1='{margin}' y1='{h-margin}' x2='{w-margin}' y2='{h-margin}' stroke='#999'/>"
            f"<line x1='{margin}' y1='{margin}' x2='{margin}' y2='{h-margin}' stroke='#999'/>"
            f"{bars}</g>")


def _draw_columnchart(x, y, w, h, label):
    margin = 20
    bars = ""
    colors = ["#4CAF50", "#2196F3", "#FFC107", "#FF5722", "#9C27B0"]
    bw = max(8, (w-2*margin)/5 - 10)
    for i in range(5):
        bh = random.randint(20, max(21, int(h*0.7)))
        bx = margin + i * (bw + 10)
        by = h - margin - bh
        bars += f"<rect x='{bx}' y='{by}' width='{bw}' height='{bh}' fill='{colors[i]}'/>"
    return (f"<g transform='translate({x},{y})'>"
            f"<rect width='{w}' height='{h}' fill='#fff' stroke='#ccc' rx='6' ry='6'/>"
            f"<text x='10' y='18' font-family='Segoe UI' font-size='12' fill='#333'>{label}</text>"
            f"<line x1='{margin}' y1='{h-margin}' x2='{w-margin}' y2='{h-margin}' stroke='black'/>"
            f"{bars}</g>")


def _draw_donutchart(x, y, w, h, label):
    cx = w/2; cy = h/2; r = min(w, h)/2-10; ir = r*0.6
    return (f"<g transform='translate({x},{y})'>"
            f"<rect width='{w}' height='{h}' fill='#fff' stroke='#ccc' rx='6' ry='6'/>"
            f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='#FF6384'/>"
            f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='#36A2EB' clip-path='inset(0 0 50% 0)'/>"
            f"<circle cx='{cx}' cy='{cy}' r='{ir}' fill='#fff'/>"
            f"</g>")


def _draw_piechart(x, y, w, h, label):
    cx = w/2; cy = h/2; r = min(w,h)/2-10
    colors = ["#FF6384","#36A2EB","#FFCE56","#4BC0C0"]
    paths = ""
    start = 0
    for i, angle in enumerate([90,90,90,90]):
        end = start + angle
        x1 = cx + r*math.cos(math.radians(start)); y1 = cy + r*math.sin(math.radians(start))
        x2 = cx + r*math.cos(math.radians(end)); y2 = cy + r*math.sin(math.radians(end))
        paths += f"<path d='M {cx},{cy} L {x1},{y1} A {r},{r} 0 0,1 {x2},{y2} Z' fill='{colors[i]}'/>"
        start = end
    return (f"<g transform='translate({x},{y})'>"
            f"<rect width='{w}' height='{h}' fill='#fff' stroke='#ccc' rx='6' ry='6'/>"
            f"{paths}</g>")


def _draw_funnel(x, y, w, h, label):
    steps = ["Inicio","Interés","Evaluación","Compra"]
    colors = ["#FFCDD2","#F8BBD0","#E1BEE7","#D1C4E9"]
    parts = ""
    tw = w*0.8; sh = h/len(steps)
    for i, step in enumerate(steps):
        sw = tw*(1-i*0.2); sx = (w-sw)/2; sy = i*sh
        parts += f"<rect x='{sx}' y='{sy}' width='{sw}' height='{sh-5}' fill='{colors[i]}' rx='4'/>"
        parts += f"<text x='{w/2}' y='{sy+sh/2}' font-size='11' text-anchor='middle' fill='#333'>{step}</text>"
    return f"<g transform='translate({x},{y})'>{parts}</g>"


def _draw_textbox(x, y, w, h, label):
    return (f"<g transform='translate({x},{y})'>"
            f"<rect width='{w}' height='{h}' fill='none' stroke='#999' rx='4' ry='4'/>"
            f"<text x='10' y='{h/2+5}' font-family='Segoe UI' font-size='13' fill='#333'>{label}</text>"
            f"</g>")


def _draw_ribbonchart(x, y, w, h, label):
    return (f"<g transform='translate({x},{y})'>"
            f"<rect width='{w}' height='{h}' fill='#fff' stroke='#ccc' rx='6' ry='6'/>"
            f"<path d='M10,20 C{w/2},20 {w/2},{h-20} {w-10},{h-20}' stroke='#4BC0C0' stroke-width='15' fill='none' opacity='0.6'/>"
            f"<path d='M10,{h-20} C{w/2},{h-20} {w/2},20 {w-10},20' stroke='#FF6384' stroke-width='15' fill='none' opacity='0.6'/>"
            f"<text x='10' y='15' font-family='Segoe UI' font-size='12' fill='#333'>{label}</text>"
            f"</g>")


def _draw_card(x, y, w, h, label):
    return (f"<g transform='translate({x},{y})'>"
            f"<rect width='{w}' height='{h}' fill='#e8f5e9' stroke='#ccc' rx='6' ry='6'/>"
            f"<text x='{w/2}' y='{h/2-5}' font-family='Segoe UI' font-size='18' fill='#2e7d32' text-anchor='middle'>1,234</text>"
            f"<text x='{w/2}' y='{h/2+15}' font-family='Segoe UI' font-size='11' fill='#666' text-anchor='middle'>{label}</text>"
            f"</g>")


def _draw_areachart(x, y, w, h, label):
    margin = 20
    pts = [(0,60),(40,40),(80,70),(120,30),(160,50)]
    pd = f"M {margin},{h-margin} "
    for px, py in pts:
        pd += f"L {margin+px},{h-margin-py} "
    pd += f"L {margin+pts[-1][0]},{h-margin} Z"
    return (f"<g transform='translate({x},{y})'>"
            f"<rect width='{w}' height='{h}' fill='#f1f8e9' stroke='#558b2f' rx='6' ry='6'/>"
            f"<path d='{pd}' fill='rgba(85,139,47,0.5)' stroke='#558b2f' stroke-width='2'/>"
            f"<text x='10' y='18' font-family='Segoe UI' font-size='12' fill='#333'>{label}</text>"
            f"</g>")


def _draw_kpi(x, y, w, h, label):
    return (f"<g transform='translate({x},{y})'>"
            f"<rect width='{w}' height='{h}' fill='#e0f7fa' stroke='#006064' rx='6' ry='6'/>"
            f"<text x='10' y='22' font-family='Segoe UI' font-size='11' fill='#000'>{label}</text>"
            f"<text x='10' y='{h/2+5}' font-family='Segoe UI' font-size='16' fill='green'>22.091</text>"
            f"<polygon points='{w-25},{h/2-5} {w-20},{h/2-15} {w-15},{h/2-5}' fill='green'/>"
            f"</g>")


def _draw_table(x, y, w, h, label):
    rows_svg = ""
    n = min(5, max(2, int(h/30)))
    rh = (h-30)/n
    for i in range(n):
        ry = 30 + i*rh
        rows_svg += f"<rect x='10' y='{ry}' width='{w-20}' height='{rh-5}' fill='#fff' stroke='#ddd'/>"
    return (f"<g transform='translate({x},{y})'>"
            f"<rect width='{w}' height='{h}' fill='#fefefe' stroke='#bbb' rx='4' ry='4'/>"
            f"<text x='10' y='20' font-family='Segoe UI' font-size='12' fill='#333'>{label}</text>"
            f"{rows_svg}</g>")


def _draw_line_combo(x, y, w, h, label):
    margin = 30
    bars = ""; pts = []
    n = 8; bw = max(6, (w-2*margin)/n*0.6)
    for i in range(n):
        bh = random.randint(30, max(31, int(h*0.6)))
        bx = margin + i*(w-2*margin)/n
        by = h - margin - bh
        bars += f"<rect x='{bx}' y='{by}' width='{bw}' height='{bh}' fill='steelblue'/>"
        ly = h - margin - random.randint(20, max(21, int(h*0.5)))
        pts.append(f"{bx+bw/2},{ly}")
    line = f"<polyline points='{' '.join(pts)}' fill='none' stroke='deeppink' stroke-width='2'/>"
    return (f"<g transform='translate({x},{y})'>"
            f"<rect width='{w}' height='{h}' fill='#fff' stroke='#ccc' rx='6' ry='6'/>"
            f"<text x='10' y='18' font-family='Segoe UI' font-size='12' fill='#333'>{label}</text>"
            f"<line x1='{margin}' y1='{h-margin}' x2='{w-margin}' y2='{h-margin}' stroke='black'/>"
            f"{bars}{line}</g>")


def _draw_bci_calendar(x, y, w, h, label):
    return (f"<g transform='translate({x},{y})'>"
            f"<rect width='{w}' height='{h}' fill='#fff' stroke='#ccc' rx='6' ry='6'/>"
            f"<text x='10' y='20' font-family='Segoe UI' font-size='14' fill='#333'>{label}</text>"
            f"<text x='{w/2}' y='{h/2}' font-family='Segoe UI' font-size='11' fill='#999' text-anchor='middle'>Calendario</text>"
            f"</g>")


def _draw_linechart(x, y, w, h, label):
    margin = 20
    pts = []
    for i in range(8):
        px = margin + i*(w-2*margin)/7
        py = h - margin - random.randint(15, max(16, int(h*0.7)))
        pts.append(f"{px},{py}")
    return (f"<g transform='translate({x},{y})'>"
            f"<rect width='{w}' height='{h}' fill='#fff' stroke='#ccc' rx='6' ry='6'/>"
            f"<text x='10' y='18' font-family='Segoe UI' font-size='12' fill='#333'>{label}</text>"
            f"<polyline points='{' '.join(pts)}' fill='none' stroke='#1a73e8' stroke-width='2'/>"
            f"<line x1='{margin}' y1='{h-margin}' x2='{w-margin}' y2='{h-margin}' stroke='#ccc'/>"
            f"</g>")


def _draw_treemap(x, y, w, h, label):
    colors = ["#4CAF50","#2196F3","#FFC107","#FF5722","#9C27B0"]
    rects = ""
    rects += f"<rect x='2' y='25' width='{w*0.6-4}' height='{h*0.6-25}' fill='{colors[0]}' rx='3'/>"
    rects += f"<rect x='{w*0.6}' y='25' width='{w*0.4-2}' height='{h*0.4-25}' fill='{colors[1]}' rx='3'/>"
    rects += f"<rect x='{w*0.6}' y='{h*0.4}' width='{w*0.4-2}' height='{h*0.2}' fill='{colors[2]}' rx='3'/>"
    rects += f"<rect x='2' y='{h*0.6}' width='{w*0.4-4}' height='{h*0.4-2}' fill='{colors[3]}' rx='3'/>"
    rects += f"<rect x='{w*0.4}' y='{h*0.6}' width='{w*0.6}' height='{h*0.4-2}' fill='{colors[4]}' rx='3'/>"
    return (f"<g transform='translate({x},{y})'>"
            f"<rect width='{w}' height='{h}' fill='#fff' stroke='#ccc' rx='6' ry='6'/>"
            f"<text x='10' y='18' font-family='Segoe UI' font-size='12' fill='#333'>{label}</text>"
            f"{rects}</g>")


def _draw_map_visual(x, y, w, h, label):
    return (f"<g transform='translate({x},{y})'>"
            f"<rect width='{w}' height='{h}' fill='#e8eaf6' stroke='#5c6bc0' rx='6' ry='6'/>"
            f"<text x='{w/2}' y='{h/2}' font-family='Segoe UI' font-size='12' fill='#333' text-anchor='middle'>Mapa: {label}</text>"
            f"</g>")


def _draw_waterfall(x, y, w, h, label):
    margin = 20; bars = ""
    vals = [40, -15, -10, 25, -5, 35]
    bw = max(6, (w-2*margin)/len(vals)-5)
    cumul = 0
    for i, v in enumerate(vals):
        bx = margin + i*(bw+5)
        if v >= 0:
            by = h - margin - cumul - v
            bars += f"<rect x='{bx}' y='{by}' width='{bw}' height='{v}' fill='#4CAF50'/>"
        else:
            by = h - margin - cumul
            bars += f"<rect x='{bx}' y='{by}' width='{bw}' height='{-v}' fill='#F44336'/>"
        cumul += v
    return (f"<g transform='translate({x},{y})'>"
            f"<rect width='{w}' height='{h}' fill='#fff' stroke='#ccc' rx='6' ry='6'/>"
            f"<text x='10' y='18' font-family='Segoe UI' font-size='12' fill='#333'>{label}</text>"
            f"{bars}</g>")


def _draw_gauge(x, y, w, h, label):
    cx = w/2; cy = h*0.65; r = min(w,h)*0.35
    return (f"<g transform='translate({x},{y})'>"
            f"<rect width='{w}' height='{h}' fill='#fff' stroke='#ccc' rx='6' ry='6'/>"
            f"<path d='M {cx-r},{cy} A {r},{r} 0 0,1 {cx+r},{cy}' fill='none' stroke='#e0e0e0' stroke-width='12'/>"
            f"<path d='M {cx-r},{cy} A {r},{r} 0 0,1 {cx},{cy-r}' fill='none' stroke='#1a73e8' stroke-width='12'/>"
            f"<text x='{cx}' y='{cy+5}' font-family='Segoe UI' font-size='14' fill='#333' text-anchor='middle'>75%</text>"
            f"<text x='{cx}' y='{h-8}' font-family='Segoe UI' font-size='11' fill='#666' text-anchor='middle'>{label}</text>"
            f"</g>")


def _draw_scatter(x, y, w, h, label):
    dots = ""
    for _ in range(12):
        dx = random.randint(20, max(21, int(w-20)))
        dy = random.randint(25, max(26, int(h-20)))
        dots += f"<circle cx='{dx}' cy='{dy}' r='4' fill='#1a73e8' opacity='0.7'/>"
    return (f"<g transform='translate({x},{y})'>"
            f"<rect width='{w}' height='{h}' fill='#fff' stroke='#ccc' rx='6' ry='6'/>"
            f"<text x='10' y='18' font-family='Segoe UI' font-size='12' fill='#333'>{label}</text>"
            f"{dots}</g>")


def _draw_tree(x, y, w, h, label):
    return (f"<g transform='translate({x},{y})'>"
            f"<rect width='{w}' height='{h}' fill='#f3e5f5' stroke='#7b1fa2' rx='6' ry='6'/>"
            f"<text x='{w/2}' y='{h/2}' font-family='Segoe UI' font-size='12' fill='#333' text-anchor='middle'>Arbol: {label}</text>"
            f"</g>")


def _draw_image(x, y, w, h, label):
    return (f"<g transform='translate({x},{y})'>"
            f"<rect width='{w}' height='{h}' fill='#fafafa' stroke='#ddd' rx='4' ry='4'/>"
            f"<text x='{w/2}' y='{h/2}' font-family='Segoe UI' font-size='11' fill='#999' text-anchor='middle'>Imagen</text>"
            f"</g>")


def _draw_shape(x, y, w, h, label):
    return (f"<g transform='translate({x},{y})'>"
            f"<rect width='{w}' height='{h}' fill='#e3f2fd' stroke='#1565c0' rx='6' ry='6' opacity='0.5'/>"
            f"</g>")


def _draw_button(x, y, w, h, label):
    return (f"<g transform='translate({x},{y})'>"
            f"<rect width='{w}' height='{h}' fill='#1a73e8' stroke='#1565c0' rx='6' ry='6'/>"
            f"<text x='{w/2}' y='{h/2+4}' font-family='Segoe UI' font-size='12' fill='#fff' text-anchor='middle'>{label}</text>"
            f"</g>")


def _draw_default(x, y, w, h, label, tipo):
    estilos = {
        "textbox": ("#fff3e0", "#e65100"),
        "card": ("#e8f5e9", "#2e7d32"),
        "funnel": ("#ede7f6", "#5e35b1"),
        "chicletslicer": ("#fffde7", "#fbc02d"),
        "kpi": ("#e0f7fa", "#006064"),
    }
    fill, stroke = estilos.get(tipo, ("#eeeeee", "#999999"))
    return (f"<g transform='translate({x},{y})'>"
            f"<rect width='{w}' height='{h}' fill='{fill}' stroke='{stroke}' stroke-width='1.5' rx='6' ry='6'/>"
            f"<text x='{w/2}' y='{h/2}' font-family='Segoe UI' font-size='11' fill='#555' text-anchor='middle' dominant-baseline='middle'>{label}</text>"
            f"</g>")


# ──────────────────────────────────────────────────────────────────────
# HTML generation
# ──────────────────────────────────────────────────────────────────────

CSS = """
<style>
  :root { --accent: #1a73e8; --bg: #f8f9fa; --card-bg: #fff; --border: #dee2e6; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: #333; padding: 40px; line-height: 1.5; }
  h1 { color: var(--accent); font-size: 1.8rem; border-bottom: 3px solid var(--accent); padding-bottom: 8px; margin-bottom: 24px; }
  h2 { color: #333; font-size: 1.3rem; margin-top: 32px; margin-bottom: 12px; border-left: 4px solid var(--accent); padding-left: 10px; }
  h3 { color: #555; font-size: 1.1rem; margin-top: 20px; margin-bottom: 8px; }
  .card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
  .kpi-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 12px; margin-bottom: 20px; }
  .kpi-box { background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 14px; text-align: center; }
  .kpi-box .value { font-size: 1.6rem; font-weight: 700; color: var(--accent); }
  .kpi-box .label { font-size: 0.8rem; color: #666; margin-top: 4px; }
  table.data-table { width: 100%; border-collapse: collapse; margin-bottom: 16px; font-size: 0.9rem; }
  table.data-table th { background: var(--accent); color: #fff; text-align: left; padding: 8px 12px; }
  table.data-table td { padding: 8px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }
  table.data-table tr:nth-child(even) { background: #f1f3f5; }
  .tag { display: inline-block; background: #e8f0fe; color: var(--accent); border-radius: 4px; padding: 2px 8px; margin: 2px; font-size: 0.82rem; }
  .tag-measure { background: #fef3e0; color: #e65100; }
  .svg-container { overflow-x: auto; margin: 12px 0; border: 1px solid var(--border); border-radius: 8px; padding: 8px; background: #fff; }
  .dax-code { background: #1e1e1e; color: #d4d4d4; padding: 12px; border-radius: 6px; font-family: 'Cascadia Code','Consolas',monospace; font-size: 0.85rem; white-space: pre-wrap; overflow-x: auto; max-width: 600px; }
  .m-code { background: #1e1e1e; color: #ce9178; padding: 12px; border-radius: 6px; font-family: 'Cascadia Code','Consolas',monospace; font-size: 0.85rem; white-space: pre-wrap; overflow-x: auto; }
  .page-section { border-top: 2px solid var(--border); padding-top: 20px; margin-top: 28px; }
  .hidden-badge { background: #e0e0e0; color: #666; font-size: 0.75rem; padding: 2px 6px; border-radius: 4px; margin-left: 6px; }
  footer { margin-top: 40px; text-align: center; color: #999; font-size: 0.8rem; }
</style>
"""


def generate_report_html(con, report_name: str) -> str:
    """Genera el HTML completo de documentación para un informe, todo desde DuckDB."""

    report = _get_report(con, report_name)
    if not report:
        return f"<html><body><h1>Error</h1><p>No se encontró el informe '{_esc(report_name)}'.</p></body></html>"

    report_id = report["id"]

    sm = _find_semantic_model(con, report)
    sm_display_name = sm["name"].replace(".SemanticModel", "") if sm else "N/A"
    sm_id = sm["id"] if sm else None

    kpis = _get_kpis(con, report_id, report_name)
    related = _find_reports_sharing_model(con, report, sm)
    measure_dax = _get_measure_dax_lookup(con, sm_id) if sm_id else {}
    pages = _get_pages(con, report_name)
    all_columns = _get_all_columns(con, report_id)
    all_measures = _get_all_measures(con, report_id)

    # ── Construir HTML ───────────────────────────────────────────────
    parts = []
    parts.append("<!DOCTYPE html>\n<html lang='es'>\n<head>\n<meta charset='utf-8'/>")
    parts.append(f"<title>Documentación – {_esc(report_name)}</title>")
    parts.append(CSS)
    parts.append("</head>\n<body>")

    # ── 1. Cabecera ──────────────────────────────────────────────────
    parts.append(f"<h1>Informe: {_esc(report_name)}</h1>")
    parts.append("<div class='card'>")
    parts.append(f"<p><strong>Nombre:</strong> {_esc(report_name)}</p>")
    parts.append(f"<p><strong>ID interno:</strong> {_esc(report.get('report_id', 'N/A'))}</p>")
    parts.append(f"<p><strong>Modelo semántico:</strong> {_esc(sm_display_name)}</p>")
    if sm:
        parts.append(f"<p><strong>ID Modelo semántico:</strong> {_esc(sm.get('semantic_model_id', ''))}</p>")
    parts.append(f"<p><strong>Workspace ID:</strong> {_esc(report.get('workspace_id', 'N/A'))}</p>")
    parts.append("</div>")

    # ── 2. KPIs ──────────────────────────────────────────────────────
    parts.append("<h2>KPIs del Informe</h2>")
    parts.append("<div class='kpi-grid'>")
    for val, lbl in [
        (kpis["pages"], "Páginas"),
        (kpis["visuals"], "Visuales"),
        (kpis["tables"], "Tablas usadas"),
        (kpis["columns"], "Columnas usadas"),
        (kpis["measures"], "Métricas usadas"),
    ]:
        parts.append(f"<div class='kpi-box'><div class='value'>{val}</div><div class='label'>{lbl}</div></div>")
    parts.append("</div>")

    # ── 3. Informes asociados al modelo semántico ────────────────────
    parts.append("<h2>Informes asociados al modelo semántico</h2>")
    parts.append("<div class='card'>")
    if related:
        parts.append(f"<p>Se han encontrado <strong>{len(related)}</strong> informe(s) adicional(es) "
                     f"que comparten el modelo <em>{_esc(sm_display_name)}</em>:</p><ul>")
        for r in related:
            parts.append(f"<li>{_esc(r)}</li>")
        parts.append("</ul>")
    else:
        parts.append(f"<p>Este es el <strong>único informe</strong> asociado al modelo "
                     f"<em>{_esc(sm_display_name)}</em>.</p>")
    parts.append("</div>")

    # ── 4. Detalle por Página ────────────────────────────────────────
    parts.append("<h2>Detalle por Página</h2>")

    for page_idx, page in enumerate(pages, 1):
        page_name = page["name"]
        page_label = page.get("display_name") or page_name
        is_hidden = not page.get("is_visible", True)
        vis_badge = " <span class='hidden-badge'>OCULTA</span>" if is_hidden else ""

        parts.append("<div class='page-section'>")
        parts.append(f"<h3>Página {page_idx}: {_esc(page_label)}{vis_badge}</h3>")

        # 4.1  SVG Mockup
        visuals = _get_visuals(con, report_id, page_name)
        parts.append("<div class='svg-container'>")
        try:
            svg = _generate_svg_from_db(page, visuals)
            parts.append(svg)
        except Exception as e:
            parts.append(f"<p style='color:red;'>Error generando SVG: {_esc(str(e))}</p>")
        parts.append("</div>")

        # 4.2  Tablas con columnas / medidas de la página
        page_columns = _get_columns_by_page(con, report_id, page_name)
        page_measures = _get_measures_by_page(con, report_id, page_name)
        all_tables_in_page = sorted(set(list(page_columns.keys()) + list(page_measures.keys())))

        if all_tables_in_page:
            parts.append("<h3>Tablas, columnas y métricas de la página</h3>")
            parts.append("<div class='card'>")
            for tbl in all_tables_in_page:
                cols = sorted(page_columns.get(tbl, []))
                meas = sorted(page_measures.get(tbl, []))
                if cols:
                    parts.append(f"<p><strong>{_esc(tbl)}</strong> ({_esc(', '.join(cols))})</p>")
                if meas:
                    tags = "".join(f"<span class='tag tag-measure'>{_esc(m)}</span>" for m in meas)
                    parts.append(f"<p><strong>{_esc(tbl)}</strong> [Métricas] {tags}</p>")
            parts.append("</div>")

        # 4.3  Métricas con DAX
        page_measure_refs = set()
        for tbl, meas_set in page_measures.items():
            for m in meas_set:
                page_measure_refs.add(f"{tbl}.{m}")

        if page_measure_refs:
            parts.append("<h3>Métricas usadas – código DAX</h3>")
            parts.append("<table class='data-table'><thead><tr><th>Tabla</th><th>Métrica</th><th>Expresión DAX</th></tr></thead><tbody>")
            for ref in sorted(page_measure_refs):
                t, m = ref.split(".", 1) if "." in ref else ("", ref)
                dax = measure_dax.get(ref, "")
                if not dax:
                    for key, val in measure_dax.items():
                        if key.endswith(f".{m}"):
                            dax = val
                            break
                dax_display = f"<div class='dax-code'>{_esc(dax)}</div>" if dax else "<em>No disponible</em>"
                parts.append(f"<tr><td>{_esc(t)}</td><td>{_esc(m)}</td><td>{dax_display}</td></tr>")
            parts.append("</tbody></table>")

        parts.append("</div>")  # page-section

    # ── 5. Inventario de tablas con código M ─────────────────────────
    parts.append("<h2>Inventario de tablas usadas en el informe</h2>")
    all_used_tables = sorted(set(list(all_columns.keys()) + list(all_measures.keys())))

    if all_used_tables:
        for tbl_name in all_used_tables:
            parts.append("<div class='card'>")
            parts.append(f"<h3>{_esc(tbl_name)}</h3>")

            m_code = _get_partition_m_code(con, sm_id, tbl_name) if sm_id else None
            if m_code:
                parts.append(f"<div class='m-code'>{_esc(m_code)}</div>")
            else:
                parts.append("<p><em>Código M no disponible (tabla calculada o modelo no encontrado en la BD)</em></p>")
            parts.append("</div>")
    else:
        parts.append("<div class='card'><p>No se detectaron tablas usadas en el informe.</p></div>")

    # ── Footer ───────────────────────────────────────────────────────
    parts.append(f"<footer>Generado automáticamente por <strong>documenta_report.py</strong> "
                 f"– {datetime.now().strftime('%Y-%m-%d %H:%M')}</footer>")
    parts.append("</body>\n</html>")

    return "\n".join(parts)


# ──────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Genera documentación HTML de informes Power BI desde DuckDB."
    )
    parser.add_argument(
        "--db", type=str, required=True,
        help="Ruta a la base de datos DuckDB (ej: data/powerbi.duckdb)"
    )
    parser.add_argument(
        "--report", type=str, default=None,
        help="Nombre del informe a documentar (ej: 'FullAdventureWorks')"
    )
    parser.add_argument(
        "--all", action="store_true", default=False,
        help="Generar documentación para todos los informes de la BD"
    )
    parser.add_argument(
        "--output-dir", type=str, default=None,
        help="Directorio donde guardar los ficheros HTML. Si no se indica y es un "
             "solo informe, se imprime por stdout."
    )
    parser.add_argument(
        "--list", action="store_true", default=False, dest="list_reports",
        help="Listar todos los informes disponibles y salir"
    )
    args = parser.parse_args()

    db_path = os.path.abspath(args.db)
    if not os.path.isfile(db_path):
        print(f"ERROR: La base de datos '{db_path}' no existe.", file=sys.stderr)
        sys.exit(1)

    con = duckdb.connect(db_path, read_only=True)

    # Modo listar
    if args.list_reports:
        names = _get_all_report_names(con)
        print(f"Informes disponibles ({len(names)}):\n")
        for n in names:
            print(f"  - {n}")
        con.close()
        return

    # Validar que se especificó --report o --all
    if not args.report and not args.all:
        parser.error("Debe especificar --report <nombre> o --all (o --list para listar)")

    # Determinar qué informes procesar
    if args.all:
        report_names = _get_all_report_names(con)
        if not report_names:
            print("No hay informes en la base de datos.", file=sys.stderr)
            con.close()
            sys.exit(1)
        print(f"Generando documentación para {len(report_names)} informe(s)...")
    else:
        report_names = [args.report]

    # Directorio de salida
    output_dir = args.output_dir
    if output_dir:
        output_dir = os.path.abspath(output_dir)
        os.makedirs(output_dir, exist_ok=True)

    generated_paths = set()
    for report_name in report_names:
        html_output = generate_report_html(con, report_name)

        if output_dir:
            safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in report_name).strip()
            output_path = os.path.join(output_dir, f"{safe_name}.html")
            # Desambiguar si hay colisión de nombres
            counter = 2
            while output_path in generated_paths:
                output_path = os.path.join(output_dir, f"{safe_name}_{counter}.html")
                counter += 1
            generated_paths.add(output_path)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_output)
            print(f"  OK {report_name}  ->  {output_path}")
        else:
            print(html_output)

    con.close()

    if output_dir:
        print(f"\nDocumentación generada en: {output_dir}")


if __name__ == "__main__":
    main()
