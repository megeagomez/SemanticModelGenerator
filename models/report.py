"""
Report - Clases para analizar y trabajar con archivos .Report de Power BI
Incluye Visual, Page, FilterMixin y clsReport (clase principal)
"""

import json
import os
import re
import math
import random
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict


class Visual:
    """Representa un visual dentro de una página del informe."""

    def __init__(self, visual_dir: str):
        self.visual_path = os.path.join(visual_dir, 'visual.json')
        self.name = None
        self.visualType = None
        self.text = None
        self.navigationTarget = None
        self.position = {}
        self.columns_used = []
        self.measures_used = []
        
        try:
            with open(self.visual_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error al cargar visual.json: {e}")
            data = {}

        self.name = data.get("name")
        self.visualType = data.get("visual", {}).get("visualType")
   
        # Posición
        pos = data.get("position", {})
        self.position = {
            "x": pos.get("x", 0),
            "y": pos.get("y", 0),
            "width": pos.get("width", 100),
            "height": pos.get("height", 100)
        }

        # Texto
        text_objects = data.get("visual", {}).get("objects", {}).get("text", [])
        for obj in text_objects:
            props = obj.get("properties", {})
            if "text" in props:
                expr = props["text"].get("expr", {}).get("Literal", {}).get("Value", "")
                self.text = expr.strip("'")

        # Navegación
        visual_links = data.get("visual", {}).get("visualContainerObjects", {}).get("visualLink", [])
        for link in visual_links:
            props = link.get("properties", {})
            if "navigationSection" in props:
                nav_expr = props["navigationSection"].get("expr", {}).get("Literal", {}).get("Value", "")
                self.navigationTarget = nav_expr.strip("'")

        # Campos usados en queryState
        projections = data.get("visual", {}).get("query", {}).get("queryState", {}).get("Values", {}).get("projections", [])
        for proj in projections:
            self._extraer_campo(proj.get("field", {}))
        projections = data.get("visual", {}).get("query", {}).get("queryState", {}).get("Values", {}).get("Indicator", {}).get("projections", [])
        for proj in projections:
            self._extraer_campo(proj.get("field", {}))

        # Campos usados en sortDefinition
        sort_fields = data.get("visual", {}).get("query", {}).get("sortDefinition", {}).get("sort", [])
        for sort in sort_fields:
            self._extraer_campo(sort.get("field", {}))

        # Campos usados en objects
        objects = data.get("visual", {}).get("objects", {})
        self._buscar_campos_en_objetos(objects)
        self._buscar_campos_en_objetos(data)

    def _extraer_campo(self, field):
        """Extrae campos de tipo Column o Measure."""
        if "Column" in field:
            ref = field["Column"]
            try:
                entity = ref.get("Expression", {}).get("SourceRef", {}).get("Entity")
            except Exception:
                entity = ref
            try:
                prop = ref.get("Property")
            except Exception:
                prop = ref
            if entity and prop:
                self.columns_used.append(f"{entity}.{prop}")
        elif "Measure" in field:
            ref = field["Measure"]
            try:
                entity = ref.get("Expression", {}).get("SourceRef", {}).get("Entity")
            except Exception:
                entity = ref
            try:
                prop = ref.get("Property")
            except Exception:
                prop = ref
            if entity and prop:
                self.measures_used.append(f"{entity}.{prop}")

    def _buscar_campos_en_objetos(self, obj):
        """Busca recursivamente campos en objetos visuales."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in ["Measure", "Column"]:
                    if isinstance(value, dict) and "Expression" in value and "Property" in value:
                        self._extraer_campo({key: value})
                    else:
                        self._extraer_campo({key: value})
                else:
                    self._buscar_campos_en_objetos(value)
        elif isinstance(obj, list):
            for item in obj:
                self._buscar_campos_en_objetos(item)

    def __repr__(self):
        return f"Visual(name={self.name}, type={self.visualType}, columns={len(self.columns_used)}, measures={len(self.measures_used)})"


class FilterMixin:
    """Mixin para extraer descripciones legibles de filtros desde configuraciones JSON."""

    def extract_filter_descriptions(self, filter_config: Dict[str, Any]) -> List[str]:
        description = []
        filters = filter_config.get("filters", []) if filter_config else []

        for f in filters:
            name = f.get("name", "Unnamed Filter")
            field = f.get("field", {}).get("Column", {})
            entity = field.get("Expression", {}).get("SourceRef", {}).get("Entity", "UnknownEntity")
            column = field.get("Property", "UnknownColumn")
            filter_obj = f.get("filter", {})
            where_clauses = filter_obj.get("Where", [])

            for clause in where_clauses:
                condition = clause.get("Condition", {})
                desc = self._describe_condition(condition, entity, column)
                if desc:
                    description.append(f"Filtro '{name}': {desc}")
        return description

    def _describe_condition(self, condition: Dict[str, Any], entity: str, column: str) -> str:
        """Genera una descripción legible de una condición de filtro."""
        try:
            if "Not" in condition:
                expr = condition["Not"].get("Expression", {})
                if "In" in expr:
                    values = expr["In"].get("Values", [])
                    val = values[0][0]["Literal"]["Value"] if values and values[0] else "?"
                    return f"Se excluyen valores {val} en '{entity}'.'{column}'."
            elif "In" in condition:
                values = condition["In"].get("Values", [])
                val = values[0][0]["Literal"]["Value"] if values and values[0] else "?"
                return f"Se incluyen solo valores {val} en '{entity}'.'{column}'."
            elif "Equals" in condition:
                right = condition["Equals"].get("Right", {})
                val = right.get("Literal", {}).get("Value", "?")
                return f"Se filtra donde '{entity}'.'{column}' es igual a {val}."
        except Exception as e:
            return f"Error al interpretar condición: {e}"
        return "Condición de filtro no reconocida o no soportada."


class Page(FilterMixin):
    """Representa una página de un informe, incluyendo sus visuales."""

    def __init__(self, page_dir: str):
        page_file = os.path.join(page_dir, 'page.json')
        try:
            with open(page_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error al cargar página: {e}")
            data = {}

        self.name = data.get("name")
        self.displayName = data.get("displayName")
        self.displayOption = data.get("displayOption")
        self.height = data.get("height")
        self.width = data.get("width")
        self.pageBinding = data.get("pageBinding")
        self.objects = data.get("objects")
        self.visibility = data.get("visibility")
        self.filterConfig = data.get("filterConfig", {})

        self.filters = self.extract_filter_descriptions(self.filterConfig)
        self.visuals: List[Visual] = []
        self._load_visuals(page_dir)

    def _load_visuals(self, page_dir: str):
        """Carga los visuales de la página desde la carpeta 'visuals'."""
        visuals_dir = os.path.join(page_dir, 'visuals')
        if not os.path.isdir(visuals_dir):
            return

        for visual_id in os.listdir(visuals_dir):
            visual_path = os.path.join(visuals_dir, visual_id)
            if os.path.isdir(visual_path):
                self.visuals.append(Visual(visual_path))

    def get_all_columns_used(self) -> Set[str]:
        """Retorna el conjunto de todas las columnas usadas en la página."""
        columns = set()
        for visual in self.visuals:
            columns.update(visual.columns_used)
        return columns

    def get_all_measures_used(self) -> Set[str]:
        """Retorna el conjunto de todas las medidas usadas en la página."""
        measures = set()
        for visual in self.visuals:
            measures.update(visual.measures_used)
        return measures

    def draw_slicer(self, visual, x, y, w, h, label):
        return f"""
        <g transform='translate({x},{y})'>
            <rect width='{w}' height='{h}' rx='8' ry='8' fill='#f4f4f4' stroke='#ccc'/>
            <text x='10' y='20' font-family='Segoe UI' font-size='14' fill='#333'>{label}</text>
            <rect x='10' y='30' width='{w - 20}' height='30' rx='4' ry='4' fill='#fff' stroke='#aaa'/>
            <text x='15' y='50' font-family='Segoe UI' font-size='13' fill='#666'>Seleccione una opción</text>
            <polygon points='{w - 25},45 {w - 30},40 {w - 20},40' fill='#666'/>
        </g>
        """

    def draw_clusteredcolumnchart(self, visual, x, y, w, h, label):
        margin = 20
        bar_width = 10
        spacing = 5
        cluster_spacing = (w - 2 * margin) / 4
        valores = [[30, 50, 70], [40, 60, 80], [20, 90, 60], [50, 30, 40]]
        colores = ["rgb(0,100,150)", "rgb(50,130,130)", "rgb(100,160,110)"]
        columnas_svg = []

        for i, grupo in enumerate(valores):
            for j, valor in enumerate(grupo):
                col_x = margin + i * cluster_spacing + j * (bar_width + spacing)
                col_y = h - margin - valor
                columnas_svg.append(f'<rect x="{col_x}" y="{col_y}" width="{bar_width}" height="{valor}" fill="{colores[j]}"/>')
            label_x = margin + i * cluster_spacing + bar_width
            label_y = h - margin + 15
            columnas_svg.append(f'<text x="{label_x}" y="{label_y}" font-size="10" text-anchor="middle">Group {i+1}</text>')

        ejes_svg = f'''
        <line x1="{margin}" y1="{h - margin}" x2="{w - margin}" y2="{h - margin}" stroke="black"/>
        <line x1="{margin}" y1="{margin}" x2="{margin}" y2="{h - margin}" stroke="black"/>
        '''
        return f'''
        <g transform="translate({x},{y})">
            {ejes_svg}
            {''.join(columnas_svg)}
        </g>
        '''

    def draw_donutchart(self, visual, x, y, w, h, label):
        cx = w / 2
        cy = h / 2
        outer_r = min(w, h) / 2 - 10
        inner_r = outer_r * 0.6
        return f"""
        <g transform='translate({x},{y})'>
            <circle cx='{cx}' cy='{cy}' r='{outer_r}' fill='#eee'/>
            <path d='M {cx + outer_r},{cy} A {outer_r},{outer_r} 0 0,1 {cx - 30},{cy + outer_r * 0.95} L {cx},{cy} Z' fill='#FF6384'/>
            <text x='{cx + 70}' y='{cy + outer_r * 0.95}' font-size='12' text-anchor='middle' fill='#333'>A</text>
            <path d='M {cx - 30},{cy + outer_r * 0.95} A {outer_r},{outer_r} 0 0,1 {cx - outer_r},{cy} L {cx},{cy} Z' fill='#36A2EB'/>
            <text x='{cx - outer_r + 10}' y='{cy + outer_r * 0.6}' font-size='12' text-anchor='middle' fill='#333'>B</text>
            <path d='M {cx - outer_r},{cy} A {outer_r},{outer_r} 0 0,1 {cx},{cy - outer_r} L {cx},{cy} Z' fill='#FFCE56'/>
            <text x='{cx - outer_r * 0.6}' y='{cy - outer_r + 10}' font-size='12' text-anchor='middle' fill='#333'>C</text>
            <path d='M {cx},{cy - outer_r} A {outer_r},{outer_r} 0 0,1 {cx + outer_r},{cy} L {cx},{cy} Z' fill='#4BC0C0'/>
            <text x='{cx + outer_r * 0.6}' y='{cy - outer_r + 10}' font-size='12' text-anchor='middle' fill='#333'>D</text>
            <circle cx='{cx}' cy='{cy}' r='{inner_r}' fill='#f9f9f9'/>
        </g>
        """

    def draw_columnchart(self, visual, x, y, w, h, label):
        margin = 20
        bar_width = (w - 2 * margin) / 5 - 10
        valores = [40, 80, 60, 90, 50]
        colores = ["#4CAF50", "#2196F3", "#FFC107", "#FF5722", "#9C27B0"]
        columnas_svg = []

        for i, valor in enumerate(valores):
            col_x = margin + i * (bar_width + 10)
            col_y = h - margin - valor
            columnas_svg.append(f'<rect x="{col_x}" y="{col_y}" width="{bar_width}" height="{valor}" fill="{colores[i]}"/>')
            columnas_svg.append(f'<text x="{col_x + bar_width/2}" y="{h - margin + 15}" font-size="10" text-anchor="middle">Cat {i+1}</text>')

        eje_svg = f'''
        <line x1="{margin}" y1="{h - margin}" x2="{w - margin}" y2="{h - margin}" stroke="black"/>
        <line x1="{margin}" y1="{margin}" x2="{margin}" y2="{h - margin}" stroke="black"/>
        '''
        return f'''
        <g transform="translate({x},{y})">
            {eje_svg}
            {''.join(columnas_svg)}
        </g>
        '''

    def draw_funnel(self, visual, x, y, w, h, label):
        funnel_svg = []
        steps = ["Inicio", "Interés", "Evaluación", "Compra"]
        colors = ["#FFCDD2", "#F8BBD0", "#E1BEE7", "#D1C4E9"]
        top_width = w * 0.8
        step_height = h / len(steps)
        for i, step in enumerate(steps):
            tw = top_width * (1 - i * 0.2)
            x_pos = (w - tw) / 2
            y_pos = i * step_height
            funnel_svg.append(f'<rect x="{x_pos}" y="{y_pos}" width="{tw}" height="{step_height - 5}" fill="{colors[i]}" rx="4" ry="4"/>')
            funnel_svg.append(f'<text x="{w/2}" y="{y_pos + step_height/2}" font-size="12" text-anchor="middle" fill="#333">{step}</text>')

        return f"""
        <g transform='translate({x},{y})'>
            {''.join(funnel_svg)}
        </g>
        """

    def draw_textbox(self, visual, x, y, w, h, label):
        return f"""
        <g transform='translate({x},{y})'>
            <rect width='{w}' height='{h}' fill='none' stroke='#999' rx='4' ry='4'/>
            <text x='{w/2}' y='{h/2}' font-family='Segoe UI' font-size='14' fill='#333' text-anchor='middle' dominant-baseline='middle'>{label}</text>
        </g>
        """

    def draw_ribbonchart(self, visual, x, y, w, h, label):
        ribbon_svg = f"""
        <path d="M10,20 C{w/2},20 {w/2},{h-20} {w-10},{h-20}" stroke="#4BC0C0" stroke-width="20" fill="none" opacity="0.6"/>
        <path d="M10,{h-20} C{w/2},{h-20} {w/2},20 {w-10},20" stroke="#FF6384" stroke-width="20" fill="none" opacity="0.6"/>
        """
        return f"""
        <g transform='translate({x},{y})'>
            <rect width='{w}' height='{h}' fill='#fff' stroke='#ccc' rx='6' ry='6'/>
            <text x='10' y='15' font-family='Segoe UI' font-size='14' fill='#333'>{label}</text>
            {ribbon_svg}
        </g>
        """

    def draw_card(self, visual, x, y, w, h, label):
        valor = getattr(visual, 'value', '1234')
        tendencia = getattr(visual, 'trend', 'up')
        flecha_color = "green" if tendencia == "up" else "red"
        flecha_svg = (
            f"<polygon points='{w - 30},{h - 30} {w - 20},{h - 40} {w - 10},{h - 30}' fill='{flecha_color}'/>"
            if tendencia == "up" else
            f"<polygon points='{w - 30},{h - 40} {w - 20},{h - 30} {w - 10},{h - 40}' fill='{flecha_color}'/>"
        )
        return f"""
        <g transform='translate({x},{y})'>
            <rect width='{w}' height='{h}' fill='#e8f5e9' stroke='#ccc' rx='6' ry='6'/>
            <text x='10' y='{h/2}' font-family='Segoe UI' font-size='12' fill='#2e7d32'>{valor}</text>
            {flecha_svg}
        </g>
        """

    def draw_areachart(self, visual, x, y, w, h, label):
        margin = 20
        puntos = [(0, 80), (40, 60), (80, 90), (120, 50), (160, 70)]
        path_d = f'M {margin},{h - margin} '
        for i, (px, py) in enumerate(puntos):
            x_p = margin + px
            y_p = h - margin - py
            path_d += f'L {x_p},{y_p} '
        path_d += f'L {margin + puntos[-1][0]},{h - margin} Z'

        return f"""
        <g transform='translate({x},{y})'>
            <rect width='{w}' height='{h}' fill='#f1f8e9' stroke='#558b2f' rx='6' ry='6'/>
            <path d='{path_d}' fill='rgba(85,139,47,0.5)' stroke='#558b2f' stroke-width='2'/>
            <text x='10' y='20' font-family='Segoe UI' font-size='14' fill='#333'>{label}</text>
        </g>
        """

    def draw_piechart(self, visual, x, y, w, h, label):
        cx = w / 2
        cy = h / 2
        r = min(w, h) / 2 - 10
        slices = [
            {"angle": 90, "color": "#FF6384", "label": "A"},
            {"angle": 90, "color": "#36A2EB", "label": "B"},
            {"angle": 90, "color": "#FFCE56", "label": "C"},
            {"angle": 90, "color": "#4BC0C0", "label": "D"},
        ]

        start_angle = 0
        paths = []
        for slice in slices:
            end_angle = start_angle + slice["angle"]
            x1 = cx + r * math.cos(math.radians(start_angle))
            y1 = cy + r * math.sin(math.radians(start_angle))
            x2 = cx + r * math.cos(math.radians(end_angle))
            y2 = cy + r * math.sin(math.radians(end_angle))
            large_arc = 1 if slice["angle"] > 180 else 0
            path = f"<path d='M {cx},{cy} L {x1},{y1} A {r},{r} 0 {large_arc},1 {x2},{y2} Z' fill='{slice['color']}'/>"
            paths.append(path)
            start_angle = end_angle

        return f"""
        <g transform='translate({x},{y})'>
            <rect width='{w}' height='{h}' fill='#fff' stroke='#ccc' rx='6' ry='6'/>
            {''.join(paths)}
            <text x='10' y='20' font-family='Segoe UI' font-size='14' fill='#333'>{label}</text>
        </g>
        """

    def draw_table(self, visual, x, y, w, h, label):
        filas_svg = []
        num_filas = 5
        fila_height = (h - 30) / num_filas

        for i in range(num_filas):
            y_fila = 30 + i * fila_height
            filas_svg.append(f"<rect x='10' y='{y_fila}' width='{w - 20}' height='{fila_height - 5}' fill='#fff' stroke='#ddd'/>")
            filas_svg.append(f"<text x='15' y='{y_fila + fila_height / 2}' font-size='12' fill='#333'>Fila {i + 1}</text>")

        return f"""
        <g transform='translate({x},{y})'>
            <rect width='{w}' height='{h}' fill='#fefefe' stroke='#bbb' rx='4' ry='4'/>
            {''.join(filas_svg)}
        </g>
        """

    def draw_kpi(self, visual, x, y, w, h, label):
        valor_actual = getattr(visual, 'value', '22.091')
        valor_anterior = getattr(visual, 'previous', '15.093')
        porcentaje = getattr(visual, 'percent', '+46.37 %')

        tendencia = random.choice(['up', 'down'])
        flecha_color = 'green' if tendencia == 'up' else 'red'
        flecha_svg = (
            f"<polygon points='{w - 30},{h/2 - 10} {w - 20},{h/2 - 20} {w - 10},{h/2 - 10}' fill='{flecha_color}'/>"
            if tendencia == 'up' else
            f"<polygon points='{w - 30},{h/2 - 20} {w - 20},{h/2 - 10} {w - 10},{h/2 - 20}' fill='{flecha_color}'/>"
        )

        return f"""
        <g transform='translate({x},{y})'>
            <rect width='{w}' height='{h}' fill='#e0f7fa' stroke='#006064' rx='6' ry='6'/>
            <text x='10' y='25' font-family='Segoe UI' font-size='12' fill='#000'>{label}</text>
            <text x='10' y='{h/2}' font-family='Segoe UI' font-size='16' fill='green'>{valor_actual}</text>
            {flecha_svg}
            <text x='10' y='{h - 30}' font-family='Segoe UI' font-size='8' fill='#000'>Mes LY: <tspan fill='#000'>{valor_anterior}</tspan> <tspan fill='blue'>({porcentaje})</tspan></text>
        </g>
        """

    def draw_line_clustered_column_combo_chart(self, visual, x, y, w, h, label):
        margin = 40
        columnas = [28592, 31939, 32845, 33945, 34945, 35945, 36945, 37845, 38845, 39845]
        trafico = [21939, 22091, 22150, 22200, 22250, 22300, 22350, 22400, 22450, 22500]
        meses = ["Oct", "Nov", "Dic", "Ene", "Feb", "Mar", "Abr", "Jul", "Ago", "Sep"]

        max_val = max(max(columnas), max(trafico))
        escala = (h - 2 * margin) / max_val
        bar_width = (w - 2 * margin) / len(columnas) * 0.6
        spacing = (w - 2 * margin) / len(columnas)

        bars_svg = []
        line_points = []

        for i, (col, traf) in enumerate(zip(columnas, trafico)):
            bar_x = margin + i * spacing
            bar_h = col * escala
            bar_y = h - margin - bar_h
            bars_svg.append(f"<rect x='{bar_x}' y='{bar_y}' width='{bar_width}' height='{bar_h}' fill='steelblue'/>")

            line_x = bar_x + bar_width / 2
            line_y = h - margin - traf * escala
            line_points.append(f"{line_x},{line_y}")

            bars_svg.append(f"<text x='{bar_x + bar_width/2}' y='{h - margin + 15}' font-size='10' text-anchor='middle'>{meses[i]}</text>")

        line_path = f"<polyline points='{' '.join(line_points)}' fill='none' stroke='deeppink' stroke-width='2'/>"
        eje_x = f"<line x1='{margin}' y1='{h - margin}' x2='{w - margin}' y2='{h - margin}' stroke='black'/>"
        eje_y = f"<line x1='{margin}' y1='{margin}' x2='{margin}' y2='{h - margin}' stroke='black'/>"

        return f"""
        <g transform='translate({x},{y})'>
            <rect width='{w}' height='{h}' fill='#fff' stroke='#ccc' rx='6' ry='6'/>
            <text x='10' y='20' font-family='Segoe UI' font-size='14' fill='#333'>{label}</text>
            {eje_x}
            {eje_y}
            {''.join(bars_svg)}
            {line_path}
        </g>
        """

    def draw_bci_calendar(self, visual, x, y, w, h, label):
        dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        ventas = {
            1: 0, 2: 0, 3: 3, 4: 4, 5: 5,
            6: 6, 7: 183, 8: 98, 9: 175, 10: 10, 11: 165, 12: 12,
            13: 13, 14: 192, 15: 247, 16: 276, 17: 17, 18: 244, 19: 19,
            20: 20, 21: 230, 22: 294, 23: 0, 24: 24, 25: 258, 26: 26,
            27: 27, 28: 300, 29: 0, 30: 0, 31: 31
        }

        cell_w = w / 7
        cell_h = (h - 40) / 6
        max_venta = max(ventas.values())

        svg = [f"<g transform='translate({x},{y})'>"]
        svg.append(f"<text x='10' y='20' font-family='Segoe UI' font-size='16' fill='#333'>{label}</text>")

        for i, dia in enumerate(dias_semana):
            svg.append(f"<text x='{i * cell_w + 5}' y='40' font-size='12' font-family='Segoe UI' fill='#333'>{dia}</text>")

        dia_actual = 1
        for fila in range(1, 7):
            for col in range(7):
                if dia_actual > 31:
                    break
                venta = ventas.get(dia_actual, 0)
                intensidad = int(255 - (venta / max_venta) * 180)
                color = f"rgb({intensidad},{intensidad + 20},{255})"
                x_pos = col * cell_w
                y_pos = fila * cell_h + 40
                svg.append(f"<rect x='{x_pos}' y='{y_pos}' width='{cell_w - 2}' height='{cell_h - 2}' fill='{color}' stroke='#ccc'/>")
                svg.append(f"<text x='{x_pos + 5}' y='{y_pos + 15}' font-size='10' font-family='Segoe UI' fill='#000'>{dia_actual}</text>")
                svg.append(f"<text x='{x_pos + 5}' y='{y_pos + 30}' font-size='10' font-family='Segoe UI' fill='#000'>{venta}</text>")
                dia_actual += 1

        svg.append("</g>")
        return "\n".join(svg)

    def draw_default(self, visual, x, y, w, h, label, tipo):
        estilos = {
            "textbox": ("#fff3e0", "#e65100"),
            "card": ("#e8f5e9", "#2e7d32"),
            "funnel": ("#ede7f6", "#5e35b1"),
            "lineclusterdcolum": ("#e3f2fd", "#1e88e5"),
            "clusteredcolumchart": ("#fce4ec", "#c2185b"),
            "areachart": ("#f1f8e9", "#558b2f"),
            "chicletslicer": ("#fffde7", "#fbc02d"),
            "kpi": ("#e0f7fa", "#006064"),
            "image": ("#ffffff", "#999999"),
        }
        fill, stroke = estilos.get(tipo, ("#eeeeee", "#999999"))
        return f"""
        <rect x='{x}' y='{y}' width='{w}' height='{h}' fill='{fill}' stroke='{stroke}' stroke-width='1.5' rx='6' ry='6'/>
        <text x='{x + w/2}' y='{y + h/2}' font-family='Segoe UI' font-size='12' fill='#333' text-anchor='middle' dominant-baseline='middle'>{label}</text>
        """

    def generate_svg_page(self):
        """Genera un SVG completo de la página con todos los visuales."""
        page = self
        width = page.width or 800
        height = page.height or 600

        svg_parts = [
            f"<svg width='{width}' height='{height}' xmlns='http://www.w3.org/2000/svg'>",
            f"<rect width='{width}' height='{height}' fill='#f9f9f9' stroke='#ccc'/>",
            f"<text x='10' y='20' font-family='Segoe UI' font-size='16' fill='#333'>Página: {page.displayName or page.name}</text>"
        ]

        draw_functions = {
            "slicer": self.draw_slicer,
            "donutchart": self.draw_donutchart,
            "clusteredcolumnchart": self.draw_clusteredcolumnchart,
            "columnchart": self.draw_columnchart,
            "funnel": self.draw_funnel,
            "piechart": self.draw_piechart,
            "table": self.draw_table,
            "kpi": self.draw_kpi,
            "card": self.draw_card,
            "areachart": self.draw_areachart,
            "lineClusteredColumnComboChart": self.draw_line_clustered_column_combo_chart,
            "lineclusteredcolumncombochart": self.draw_line_clustered_column_combo_chart,
            "textbox": self.draw_textbox,
            "bci_calendar": self.draw_bci_calendar,
            "bcicalendar": self.draw_bci_calendar,
            "ribbonchart": self.draw_ribbonchart,
        }

        for visual in getattr(page, 'visuals', []):
            pos = getattr(visual, 'position', {})
            x = pos.get('x', 0)
            y = pos.get('y', 0)
            w = pos.get('width', 200)
            h = pos.get('height', 160)
            tipo = (visual.visualType or "unknown").lower()
            if tipo.startswith("bci"):
                tipo = "bcicalendar"
            label = visual.text or visual.visualType or visual.name or "Visual"

            draw_fn = draw_functions.get(tipo, lambda v, x, y, w, h, l: self.draw_default(v, x, y, w, h, l, tipo))
            svg_parts.append(draw_fn(visual, x, y, w, h, label))

        svg_parts.append("</svg>")
        return "\n".join(svg_parts)

    def __repr__(self):
        return f"Page(name={self.displayName or self.name}, visuals={len(self.visuals)})"


class clsReport(FilterMixin):
    """Clase principal para cargar y representar un informe completo."""

    def __init__(self, root_path: str):
        self.root_path = root_path
        self.report_path = self._find_report_json()
        self.pages_path = os.path.join(os.path.dirname(self.report_path), 'pages') if self.report_path else None
        
        self.schema = None
        self.themeCollection = None
        self.filterConfig = None
        self.objects = None
        self.publicCustomVisuals = None
        self.resourcePackages = None
        self.settings = None
        self.slowDataSourceSettings = None
        self.pageOrder = []
        self.activePageName = None
        self.allfilters = []
        self.pages: List[Page] = []
        self.SemanticModel = ""
        
        if self.report_path:
            self._load_report_json()
        if self.pages_path and os.path.isdir(self.pages_path):
            self._load_pages()

    def _extract_semantic_model_name(self):
        """Extrae el nombre del modelo semántico desde definition.pbir"""
        pbir_file_path = os.path.join(self.root_path, 'definition.pbir')
        if not os.path.exists(pbir_file_path):
            return None
            
        try:
            with open(pbir_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    
        dataset_ref = data.get("datasetReference", {})

        # Caso 1: byConnection
        if "byConnection" in dataset_ref:
            connection_string = dataset_ref["byConnection"].get("connectionString", "")
            match = re.search(r'Data Source="powerbi://api\.powerbi\.com/v1\.0/myorg/(.*?)"', connection_string)
            if match:
                return match.group(1)

        # Caso 2: byPath
        elif "byPath" in dataset_ref:
            path = dataset_ref["byPath"].get("path", "")
            match = re.search(r'\.\./(.*?)\.SemanticModel', path)
            if match:
                return match.group(1)
        
        return None
    
    def _find_report_json(self) -> Optional[str]:
        """Busca el archivo report.json dentro de la carpeta 'definition'."""
        for root, dirs, files in os.walk(self.root_path):
            if 'definition' in dirs:
                definition_path = os.path.join(root, 'definition')
                report_path = os.path.join(definition_path, 'report.json')
                if os.path.isfile(report_path):
                    return report_path
        return None

    def _load_report_json(self):
        """Carga el contenido del archivo report.json."""
        if not self.report_path:
            print("Error: No se encontró el archivo report.json")
            return
            
        try:
            self.SemanticModel = self._extract_semantic_model_name()
            with open(self.report_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error al cargar report.json: {e}")
            data = {}

        self.schema = data.get("$schema")
        self.themeCollection = data.get("themeCollection")
        self.filterConfig = data.get("filterConfig", {})
        self.objects = data.get("objects")
        self.publicCustomVisuals = data.get("publicCustomVisuals")
        self.resourcePackages = data.get("resourcePackages")
        self.settings = data.get("settings")
        self.slowDataSourceSettings = data.get("slowDataSourceSettings")
        self.allfilters = self.extract_filter_descriptions(self.filterConfig)

    def _load_pages(self):
        """Carga las páginas del informe desde la carpeta 'pages'."""
        if not self.pages_path:
            return
        pages_metadata_file = os.path.join(self.pages_path, 'pages.json')
        try:
            with open(pages_metadata_file, 'r', encoding='utf-8') as f:
                pages_data = json.load(f)
            self.pageOrder = pages_data.get("pageOrder", [])
            self.activePageName = pages_data.get("activePageName")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error al cargar pages.json: {e}")

        for page_id in self.pageOrder:
            page_dir = os.path.join(self.pages_path, page_id)
            page_file = os.path.join(page_dir, 'page.json')
            if os.path.isfile(page_file):
                self.pages.append(Page(page_dir))

    def get_all_columns_used(self) -> Dict[str, Set[str]]:
        """Retorna todas las columnas usadas en el informe organizadas por tabla."""
        table_columns: Dict[str, Set[str]] = defaultdict(set)
        for page in self.pages:
            for col_ref in page.get_all_columns_used():
                if '.' in col_ref:
                    table, column = col_ref.split('.', 1)
                    table_columns[table].add(column)
        return dict(table_columns)

    def get_all_measures_used(self) -> Dict[str, Set[str]]:
        """Retorna todas las medidas usadas en el informe organizadas por tabla."""
        table_measures: Dict[str, Set[str]] = defaultdict(set)
        for page in self.pages:
            for meas_ref in page.get_all_measures_used():
                if '.' in meas_ref:
                    table, measure = meas_ref.split('.', 1)
                    table_measures[table].add(measure)
        return dict(table_measures)

    def __repr__(self):
        return f"clsReport(model={self.SemanticModel}, pages={len(self.pages)})"
