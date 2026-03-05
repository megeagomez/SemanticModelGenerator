"""
ReportDocumenter – clase central para documentación y análisis de informes
Power BI almacenados en DuckDB.  Reutilizable desde Streamlit, MCP, CLI, etc.
"""

import html as html_mod
from collections import defaultdict


def _esc(text):
    if text is None:
        return ""
    return html_mod.escape(str(text))


class ReportDocumenter:
    """Documenta un informe Power BI a partir de datos en DuckDB."""

    def __init__(self, con, report_name, semantic_model_name=None):
        self.con = con
        self.report_name = report_name
        self.report = self._get_report()
        self.pages = self._get_pages() if self.report else []
        # Resolve semantic model
        if semantic_model_name:
            self._sm_name = semantic_model_name
        elif self.report:
            self._sm_name = report_name + ".SemanticModel"
        else:
            self._sm_name = None
        self.semantic_model_id = self._resolve_sm_id()

    # ── data access ──────────────────────────────────────────────────

    def _get_report(self):
        row = self.con.execute(
            "SELECT id, name, report_id, workspace_id, semantic_model_reference, "
            "schema, active_page_name FROM report WHERE name = ?",
            [self.report_name],
        ).fetchone()
        if not row:
            return None
        return dict(
            zip(
                ["id", "name", "report_id", "workspace_id",
                 "semantic_model_reference", "schema", "active_page_name"],
                row,
            )
        )

    def _get_pages(self):
        cols = ["id", "name", "display_name", "height", "width",
                "display_option", "is_visible"]
        page_cols = [c[0] for c in self.con.execute("DESCRIBE report_page").fetchall()]
        if "is_visible" not in page_cols:
            cols.remove("is_visible")
        rows = self.con.execute(
            f"SELECT {', '.join(cols)} FROM report_page WHERE report_name = ? ORDER BY id",
            [self.report_name],
        ).fetchall()
        pages = []
        for row in rows:
            d = dict(zip(cols, row))
            d.setdefault("is_visible", True)
            pages.append(d)
        return pages

    def _resolve_sm_id(self):
        if not self._sm_name:
            return None
        row = self.con.execute(
            "SELECT id FROM semantic_model WHERE name = ?", [self._sm_name]
        ).fetchone()
        return row[0] if row else None

    # ── KPIs ─────────────────────────────────────────────────────────

    def get_kpis(self):
        sm_id = self.semantic_model_id
        n_columns = self.con.execute(
            "SELECT COUNT(*) FROM semantic_model_column WHERE semantic_model_id = ?",
            [sm_id]).fetchone()[0] if sm_id else 0
        n_measures = self.con.execute(
            "SELECT COUNT(*) FROM semantic_model_measure WHERE semantic_model_id = ?",
            [sm_id]).fetchone()[0] if sm_id else 0
        n_pages = len(self.pages)
        n_tables = self.con.execute(
            "SELECT COUNT(*) FROM semantic_model_table WHERE semantic_model_id = ?",
            [sm_id]).fetchone()[0] if sm_id else 0
        n_relationships = self.con.execute(
            "SELECT COUNT(*) FROM semantic_model_relationship WHERE semantic_model_id = ?",
            [sm_id]).fetchone()[0] if sm_id else 0
        n_reports_using_model = 0
        if self._sm_name:
            n_reports_using_model = self.con.execute(
                "SELECT COUNT(*) FROM report r JOIN semantic_model sm "
                "ON sm.name = r.name || '.SemanticModel' WHERE sm.name = ?",
                [self._sm_name]).fetchone()[0]
        return {
            "columns": n_columns,
            "measures": n_measures,
            "pages": n_pages,
            "tables": n_tables,
            "relationships": n_relationships,
            "reports_using_model": n_reports_using_model,
        }

    # ── page details ─────────────────────────────────────────────────

    def get_page_details(self, page):
        rid = self.report["id"]
        pname = page["name"]

        columns = self.con.execute(
            "SELECT DISTINCT table_name, column_name FROM report_column_used "
            "WHERE report_id = ? AND page_name = ?", [rid, pname]
        ).fetchall()
        columns_by_table = defaultdict(list)
        for table, col in columns:
            columns_by_table[table].append(col)

        measures = self.con.execute(
            "SELECT DISTINCT measure_name FROM report_measure_used "
            "WHERE report_id = ? AND page_name = ?", [rid, pname]
        ).fetchall()

        dax = {}
        if self.semantic_model_id:
            for (mname,) in measures:
                row = self.con.execute(
                    "SELECT expression FROM semantic_model_measure "
                    "WHERE semantic_model_id = ? AND measure_name = ?",
                    [self.semantic_model_id, mname]).fetchone()
                if row and row[0]:
                    dax[mname] = row[0]

        m_code = {}
        if self.semantic_model_id:
            table_names = list(columns_by_table.keys())
            for tname in table_names:
                rows = self.con.execute(
                    "SELECT partition_name, source_expression FROM semantic_model_partitions "
                    "WHERE semantic_model_id = ? AND table_name = ?",
                    [self.semantic_model_id, tname]).fetchall()
                for pn, expr in rows:
                    if expr:
                        m_code[f"{tname}.{pn}"] = expr

        return {
            "columns_by_table": dict(columns_by_table),
            "measures": [m[0] for m in measures],
            "dax": dax,
            "m_code": m_code,
        }

    # ── visuals ──────────────────────────────────────────────────────

    def get_visuals(self, page):
        rows = self.con.execute(
            "SELECT name, visual_type, position_x, position_y, "
            "position_width, position_height, text_content, navigation_target "
            "FROM report_visual WHERE report_id = ? AND page_name = ? ORDER BY id",
            [self.report["id"], page["name"]],
        ).fetchall()
        cols = ["name", "visual_type", "x", "y", "width", "height",
                "text_content", "navigation_target"]
        return [dict(zip(cols, r)) for r in rows]

    # ── SVG mockup ───────────────────────────────────────────────────

    def generate_svg(self, page, visuals, scale=0.55):
        raw_w = page.get("width") or 1280
        raw_h = page.get("height") or 720
        w = int(raw_w * scale)
        h = int(raw_h * scale)

        TYPE_COLORS = {
            "slicer": ("#e8f5e9", "#388e3c"),
            "card": ("#fff3e0", "#e65100"),
            "multirowcard": ("#fff3e0", "#e65100"),
            "kpi": ("#fce4ec", "#c62828"),
            "table": ("#e3f2fd", "#1565c0"),
            "pivottable": ("#e3f2fd", "#1565c0"),
            "matrix": ("#e3f2fd", "#1565c0"),
            "matrixvisual": ("#e3f2fd", "#1565c0"),
            "clusteredcolumnchart": ("#e8eaf6", "#283593"),
            "columnchart": ("#e8eaf6", "#283593"),
            "clusteredbarchart": ("#e8eaf6", "#283593"),
            "stackedbarchart": ("#e8eaf6", "#283593"),
            "stackedcolumnchart": ("#e8eaf6", "#283593"),
            "linechart": ("#f3e5f5", "#6a1b9a"),
            "lineclusteredcolumncombochart": ("#f3e5f5", "#6a1b9a"),
            "areachart": ("#f3e5f5", "#6a1b9a"),
            "piechart": ("#fce4ec", "#ad1457"),
            "donutchart": ("#fce4ec", "#ad1457"),
            "funnel": ("#fff8e1", "#f57f17"),
            "treemap": ("#e0f2f1", "#00695c"),
            "map": ("#e0f7fa", "#00838f"),
            "filledmap": ("#e0f7fa", "#00838f"),
            "gauge": ("#fbe9e7", "#bf360c"),
            "waterfallchart": ("#efebe9", "#4e342e"),
            "scatterchart": ("#f1f8e9", "#33691e"),
            "textbox": ("#fafafa", "#616161"),
            "shape": ("#eceff1", "#455a64"),
            "image": ("#eceff1", "#455a64"),
            "actionbutton": ("#e1f5fe", "#0277bd"),
            "ribbonchart": ("#ede7f6", "#4527a0"),
            "decompositiontreevisual": ("#e0f2f1", "#004d40"),
        }
        default_fill, default_stroke = "#eaf6fb", "#0078d4"

        svg = [
            f'<svg width="{w}" height="{h}" viewBox="0 0 {raw_w} {raw_h}" '
            f'xmlns="http://www.w3.org/2000/svg" style="border:1px solid #ddd;border-radius:8px;">',
            f'<rect width="{raw_w}" height="{raw_h}" fill="#ffffff" rx="6"/>',
        ]

        for v in visuals:
            vx = v.get("x") or 0
            vy = v.get("y") or 0
            vw = v.get("width") or 200
            vh = v.get("height") or 160
            tipo = (v.get("visual_type") or "unknown").lower()
            label = _esc(v.get("text_content") or v.get("visual_type") or v.get("name") or "Visual")
            if len(label) > 28:
                label = label[:25] + "…"
            fill, stroke = TYPE_COLORS.get(tipo, (default_fill, default_stroke))
            svg.append(
                f'<rect x="{vx}" y="{vy}" width="{vw}" height="{vh}" rx="4" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="1.5" opacity="0.92"/>'
            )
            svg.append(
                f'<text x="{vx+6}" y="{vy+16}" font-family="Segoe UI,sans-serif" '
                f'font-size="11" fill="{stroke}" font-weight="600">{_esc(tipo)}</text>'
            )
            svg.append(
                f'<text x="{vx+6}" y="{vy+32}" font-family="Segoe UI,sans-serif" '
                f'font-size="10" fill="#555">{label}</text>'
            )

        svg.append("</svg>")
        return "\n".join(svg)

    # ── semantic model detail ────────────────────────────────────────

    def get_model_tables(self):
        if not self.semantic_model_id:
            return []
        rows = self.con.execute(
            "SELECT table_name, is_hidden FROM semantic_model_table "
            "WHERE semantic_model_id = ? ORDER BY table_name",
            [self.semantic_model_id]).fetchall()
        return [{"table_name": r[0], "is_hidden": r[1]} for r in rows]

    def get_model_columns(self, table_name=None):
        if not self.semantic_model_id:
            return []
        if table_name:
            rows = self.con.execute(
                "SELECT table_name, column_name, data_type, is_hidden "
                "FROM semantic_model_column WHERE semantic_model_id = ? AND table_name = ? "
                "ORDER BY table_name, column_name",
                [self.semantic_model_id, table_name]).fetchall()
        else:
            rows = self.con.execute(
                "SELECT table_name, column_name, data_type, is_hidden "
                "FROM semantic_model_column WHERE semantic_model_id = ? "
                "ORDER BY table_name, column_name",
                [self.semantic_model_id]).fetchall()
        return [{"table_name": r[0], "column_name": r[1],
                 "data_type": r[2], "is_hidden": r[3]} for r in rows]

    def get_model_measures(self):
        if not self.semantic_model_id:
            return []
        rows = self.con.execute(
            "SELECT table_name, measure_name, expression, format_string, is_hidden "
            "FROM semantic_model_measure WHERE semantic_model_id = ? "
            "ORDER BY table_name, measure_name",
            [self.semantic_model_id]).fetchall()
        return [{"table_name": r[0], "measure_name": r[1], "expression": r[2],
                 "format_string": r[3], "is_hidden": r[4]} for r in rows]

    def get_model_relationships(self):
        if not self.semantic_model_id:
            return []
        rows = self.con.execute(
            "SELECT relationship_name, from_table, from_column, to_table, to_column, "
            "cardinality, cross_filtering_behavior, is_active "
            "FROM semantic_model_relationship WHERE semantic_model_id = ? "
            "ORDER BY from_table",
            [self.semantic_model_id]).fetchall()
        return [{"name": r[0], "from_table": r[1], "from_column": r[2],
                 "to_table": r[3], "to_column": r[4], "cardinality": r[5],
                 "cross_filter": r[6], "is_active": r[7]} for r in rows]

    def get_model_partitions(self):
        if not self.semantic_model_id:
            return []
        rows = self.con.execute(
            "SELECT table_name, partition_name, source_type, mode, source_expression "
            "FROM semantic_model_partitions WHERE semantic_model_id = ? "
            "ORDER BY table_name",
            [self.semantic_model_id]).fetchall()
        return [{"table_name": r[0], "partition_name": r[1], "source_type": r[2],
                 "mode": r[3], "source_expression": r[4]} for r in rows]

    # ── unused measures ──────────────────────────────────────────────

    def get_unused_measures(self):
        """Measures defined in the model but not used in any report."""
        if not self.semantic_model_id:
            return []
        all_measures = self.con.execute(
            "SELECT table_name, measure_name, expression "
            "FROM semantic_model_measure WHERE semantic_model_id = ?",
            [self.semantic_model_id]).fetchall()
        used = self.con.execute(
            "SELECT DISTINCT rmu.measure_name "
            "FROM report_measure_used rmu "
            "JOIN report r ON rmu.report_id = r.id "
            "JOIN semantic_model sm ON sm.name = r.name || '.SemanticModel' "
            "WHERE sm.id = ?",
            [self.semantic_model_id]).fetchall()
        used_set = {u[0] for u in used}
        return [{"table_name": m[0], "measure_name": m[1], "expression": m[2]}
                for m in all_measures if m[1] not in used_set]

    # ── reports linked to a model ────────────────────────────────────

    @staticmethod
    def get_reports_for_model(con, sm_name):
        """Return list of report names that use the given semantic model."""
        rows = con.execute(
            "SELECT r.name FROM report r "
            "JOIN semantic_model sm ON sm.name = r.name || '.SemanticModel' "
            "WHERE sm.name = ?", [sm_name]).fetchall()
        return [r[0] for r in rows]

    @staticmethod
    def get_model_for_report(con, report_name):
        """Return the semantic model name for a given report."""
        sm_name = report_name + ".SemanticModel"
        row = con.execute(
            "SELECT name FROM semantic_model WHERE name = ?", [sm_name]
        ).fetchone()
        return row[0] if row else None
