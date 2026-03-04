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
        self.filterConfig = None
        self.filters: List[Filter] = []
        self.entity_alias_map = {}  # Nuevo: mapeo alias->entidad real

        try:
            with open(self.visual_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error al cargar visual.json: {e}")
            data = {}

        self.name = data.get("name")
        self.visualType = data.get("visual", {}).get("visualType")

        # Guardar mapeo de alias a entidad real si existe prototypeQuery.From
        proto_query = data.get('prototypeQuery')
        if not proto_query:
            sv= data.get("singleVisual")
            if sv and isinstance(sv, dict):
                proto_query = sv.get('prototypeQuery')
        if proto_query and isinstance(proto_query, dict):
            from_list = proto_query.get('From')
            if isinstance(from_list, list):
                for entry in from_list:
                    if isinstance(entry, dict) and 'Name' in entry and 'Entity' in entry:
                        self.entity_alias_map[entry['Name']] = entry['Entity']

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

        # Campos usados en queryState (recorrer todos los posibles apartados)
        query_state = data.get("visual", {}).get("query", {}).get("queryState", {})
        if isinstance(query_state, dict):
            for key, value in query_state.items():
                if isinstance(value, dict) and "projections" in value:
                    projections = value.get("projections", [])
                    for proj in projections:
                        self._extraer_campo(proj.get("field", {}), proj.get("queryRef"))

        # Campos usados en sortDefinition
        sort_fields = data.get("visual", {}).get("query", {}).get("sortDefinition", {}).get("sort", [])
        for sort in sort_fields:
            self._extraer_campo(sort.get("field", {}))

        # Campos usados en objects
        objects = data.get("visual", {}).get("objects", {})
        self._buscar_campos_en_objetos(objects)
        self._buscar_campos_en_objetos(data)
        
        # Filtros a nivel de visual
        self.filterConfig = data.get("filterConfig", {})
        if self.filterConfig:
            self.filters = Filter.extract_from_config(
                self.filterConfig,
                filter_type="visual",
                visual_name=self.name
            )

    def _extraer_campo(self, field, query_ref=None):
        """Extrae campos de tipo Column o Measure, usando queryRef si está presente y distinguiendo tipo. Sustituye alias por entidad real si es necesario."""
        # Si hay query_ref, usarlo y distinguir tipo
        if query_ref:
            # Resolver alias en queryRef (formato típico: "alias.Property")
            resolved_ref = query_ref
            if '.' in query_ref:
                alias_part, prop_part = query_ref.split('.', 1)
                if alias_part in self.entity_alias_map:
                    resolved_ref = f"{self.entity_alias_map[alias_part]}.{prop_part}"
            if "Measure" in field:
                self.measures_used.append(resolved_ref)
                return
            elif "Column" in field:
                self.columns_used.append(resolved_ref)
                return
        # Si no hay query_ref, parseo tradicional
        if "Column" in field:
            ref = field["Column"]
            table_name = ref.get("Table") or ref.get("Entity")
            if not table_name:
                table_name = ref.get("Expression", {}).get("SourceRef", {}).get("Entity")
                if not table_name:
                    table_name = ref.get("Expression", {}).get("SourceRef", {}).get("Source")
            # Sustituir alias por entidad real si corresponde
            if table_name and table_name in self.entity_alias_map:
                table_name = self.entity_alias_map[table_name]
            prop = ref.get("Property")
            if prop:
                self.columns_used.append(f"{table_name}.{prop}" if table_name else f"{prop}")
        elif "Measure" in field:
            ref = field["Measure"]
            table_name = ref.get("Table") or ref.get("Entity")
            if not table_name:
                table_name = ref.get("Expression", {}).get("SourceRef", {}).get("Entity")
                if not table_name:
                    table_name = ref.get("Expression", {}).get("SourceRef", {}).get("Source")
            # Sustituir alias por entidad real si corresponde
            if table_name and table_name in self.entity_alias_map:
                table_name = self.entity_alias_map[table_name]
            prop = ref.get("Property")
            if prop:
                self.measures_used.append(f"{table_name}.{prop}" if table_name else f"{prop}")

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
            # PBIR usa "field", legacy usa "expression"
            field = f.get("field", f.get("expression", {})).get("Column", {})
            entity = field.get("Expression", {}).get("SourceRef", {}).get("Entity", "")
            if not entity:
                # Resolver alias desde filter.From
                source = field.get("Expression", {}).get("SourceRef", {}).get("Source", "")
                filter_from = f.get("filter", {}).get("From", [])
                alias_map = {}
                if isinstance(filter_from, list):
                    for entry in filter_from:
                        if isinstance(entry, dict) and 'Name' in entry and 'Entity' in entry:
                            alias_map[entry['Name']] = entry['Entity']
                entity = alias_map.get(source, source) if source else "UnknownEntity"
            if not entity:
                entity = "UnknownEntity"
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


class Filter:
    """Representa un filtro con información de su origen (report, page o visual) y columnas involucradas."""

    def __init__(self, name: str, filter_type: str, table_name: str, column_name: str, 
                 page_name: str = None, visual_name: str = None, description: str = None):
        """
        Args:
            name: Nombre del filtro
            filter_type: Tipo de filtro ('report', 'page', o 'visual')
            table_name: Nombre de la tabla del campo filtrado
            column_name: Nombre de la columna filtrada
            page_name: Nombre de la página (si es page o visual filter)
            visual_name: Nombre del visual (si es visual filter)
            description: Descripción legible del filtro
        """
        self.name = name
        self.filter_type = filter_type
        self.table_name = table_name
        self.column_name = column_name
        self.page_name = page_name
        self.visual_name = visual_name
        self.description = description

    @staticmethod
    def extract_from_config(filter_config: Dict[str, Any], filter_type: str = "report",
                           page_name: str = None, visual_name: str = None) -> List['Filter']:
        """
        Extrae una lista de Filter objects desde una configuración de filtros.
        
        Args:
            filter_config: Configuración JSON de filtros
            filter_type: Tipo de filtro ('report', 'page', o 'visual')
            page_name: Nombre de la página (si es page o visual filter)
            visual_name: Nombre del visual (si es visual filter)
        
        Returns:
            Lista de objetos Filter
        """
        filters = []
        filter_list = filter_config.get("filters", []) if filter_config else []

        for f in filter_list:
            name = f.get("name", "Unnamed Filter")
            # PBIR usa "field", legacy usa "expression"
            field_container = f.get("field", f.get("expression", {}))
            
            # Intentar extraer información de Column, Measure o Aggregation
            table_name = "UnknownTable"
            column_name = "UnknownField"
            field_type_str = "field"
            
            # Construir alias_map desde filter.From si existe
            filter_from = f.get("filter", {}).get("From", [])
            alias_map = {}
            if isinstance(filter_from, list):
                for entry in filter_from:
                    if isinstance(entry, dict) and 'Name' in entry and 'Entity' in entry:
                        alias_map[entry['Name']] = entry['Entity']
            
            # Caso 1: Columna ordinaria
            if "Column" in field_container:
                field = field_container.get("Column", {})
                table_name = field.get("Expression", {}).get("SourceRef", {}).get("Entity", "")
                if not table_name:
                    source = field.get("Expression", {}).get("SourceRef", {}).get("Source", "")
                    table_name = alias_map.get(source, source) if source else "UnknownTable"
                if not table_name:
                    table_name = "UnknownTable"
                column_name = field.get("Property", "UnknownColumn")
                field_type_str = "column"
            
            # Caso 2: Medida
            elif "Measure" in field_container:
                field = field_container.get("Measure", {})
                table_name = field.get("Expression", {}).get("SourceRef", {}).get("Entity", "")
                if not table_name:
                    source = field.get("Expression", {}).get("SourceRef", {}).get("Source", "")
                    table_name = alias_map.get(source, source) if source else "UnknownTable"
                if not table_name:
                    table_name = "UnknownTable"
                column_name = field.get("Property", "UnknownMeasure")
                field_type_str = "measure"
            
            # Caso 3: Agregación
            elif "Aggregation" in field_container:
                field = field_container.get("Aggregation", {})
                # Las agregaciones tienen estructura diferente
                col_field = field.get("Expression", {}).get("Column", {})
                table_name = col_field.get("Expression", {}).get("SourceRef", {}).get("Entity", "")
                if not table_name:
                    source = col_field.get("Expression", {}).get("SourceRef", {}).get("Source", "")
                    table_name = alias_map.get(source, source) if source else "UnknownTable"
                if not table_name:
                    table_name = "UnknownTable"
                column_name = col_field.get("Property", "UnknownAggregation")
                field_type_str = "aggregation"
            
            # Generar descripción basada en condiciones
            filter_config_obj = f.get("filter", {})
            where_clauses = filter_config_obj.get("Where", [])
            descriptions = []
            
            for clause in where_clauses:
                condition = clause.get("Condition", {})
                try:
                    if "Not" in condition:
                        desc = f"Se excluyen valores en '{table_name}'.'{column_name}'"
                    elif "In" in condition:
                        desc = f"Se incluyen valores en '{table_name}'.'{column_name}'"
                    elif "Equals" in condition:
                        desc = f"Es igual a en '{table_name}'.'{column_name}'"
                    elif "Comparison" in condition:
                        comp = condition.get("Comparison", {})
                        comp_kind = comp.get("ComparisonKind", -1)
                        comparison_types = {
                            0: "igual a",
                            1: "mayor que",
                            2: "menor que",
                            3: "mayor o igual que",
                            4: "menor o igual que",
                            5: "no igual a"
                        }
                        comp_str = comparison_types.get(comp_kind, "comparación desconocida")
                        desc = f"Filtro de {field_type_str} where '{column_name}' es {comp_str}"
                    else:
                        desc = f"Condición desconocida en '{table_name}'.'{column_name}'"
                    descriptions.append(desc)
                except Exception as e:
                    descriptions.append(f"Error al procesar condición en '{table_name}'.'{column_name}': {str(e)}")
            
            description = "; ".join(descriptions) if descriptions else None
            
            # Solo crear Filter si hay información válida
            if table_name != "UnknownTable" or column_name != "UnknownField":
                filter_obj = Filter(
                    name=name,
                    filter_type=filter_type,
                    table_name=table_name,
                    column_name=column_name,
                    page_name=page_name,
                    visual_name=visual_name,
                    description=description
                )
                filters.append(filter_obj)
        
        return filters

    def __repr__(self):
        return f"Filter(name={self.name}, type={self.filter_type}, {self.table_name}.{self.column_name})"


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

        self.filter_descriptions = self.extract_filter_descriptions(self.filterConfig)
        self.filters = Filter.extract_from_config(
            self.filterConfig,
            filter_type="page",
            page_name=self.name
        )
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
            <text x='10' y='15' font-family='Segoe UI' font-size='14' fill='#333'>{label}</text>
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

    def __init__(self, root_path: str, report_id: str = None, workspace_id: str = None, report_name: str = None):
        self.root_path = root_path
        self.report_id = report_id  # ID del reporte desde Microsoft Fabric
        self.workspace_id = workspace_id  # ID del workspace desde Microsoft Fabric
        self.report_name = report_name  # Nombre del reporte (displayName desde Power BI)
        self.report_path = self._find_report_json()
        self.report_format = None  # Se establecerá en _load_report_json()
        self._report_data = None  # Almacenar datos raw del report.json
        
        # Determinar ruta de páginas basado en formato encontrado
        if self.report_path:
            report_dir = os.path.dirname(self.report_path)
            # Si report.json está en .../definition/, las páginas estarán en .../definition/pages/
            # Si report.json está en raíz, las páginas estarán en ./pages/
            potential_pages_path = os.path.join(report_dir, 'pages')
            self.pages_path = potential_pages_path if os.path.isdir(potential_pages_path) else None
        else:
            self.pages_path = None
        
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
        self.filters: List[Filter] = []
        self.pages: List[Page] = []
        self.SemanticModel = ""
        self.semantic_model_id = None
        
        if self.report_path:
            print(f"[INFO] Parseando report.json...")
            self._load_report_json()
            
            # Cargar páginas basado en el formato detectado
            print(f"[INFO] Cargando paginas...")
            self._load_pages()
        else:
            print(f"[WARN] No se pudo encontrar report.json para {root_path}")

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
            # Extraer ID del modelo semántico
            id_match = re.search(r'semanticmodelid=([a-f0-9\-]+)', connection_string)
            if id_match:
                self.semantic_model_id = id_match.group(1)
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
        """Busca el archivo report.json en dos formatos:
        1. Formato nuevo PBIR: carpeta 'definition/report.json'
        2. Formato antiguo: 'report.json' en la raíz
        """
        if not os.path.exists(self.root_path):
            print(f"⚠️ La ruta del reporte NO EXISTE: {self.root_path}")
            return None
        
        # Caso 1: Buscar en formato nuevo (PBIR) - dentro de carpeta 'definition/'
        for root, dirs, files in os.walk(self.root_path):
            if 'definition' in dirs:
                definition_path = os.path.join(root, 'definition')
                report_path = os.path.join(definition_path, 'report.json')
                if os.path.isfile(report_path):
                    print(f"[OK] Encontrado report.json (formato PBIR) en: {report_path}")
                    return report_path
        
        # Caso 2: Buscar en formato antiguo - report.json en la raíz
        report_path = os.path.join(self.root_path, 'report.json')
        if os.path.isfile(report_path):
            print(f"[OK] Encontrado report.json (formato antiguo) en: {report_path}")
            return report_path
        
        # Si no encuentra nada, mostrar información de debug
        print(f"[ERROR] report.json NO ENCONTRADO en: {self.root_path}")
        print(f"   Carpetas/archivos en raiz: {os.listdir(self.root_path) if os.path.exists(self.root_path) else 'N/A'}")
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

        # Detectar formato: PBIR (con $schema) o antiguo (con sections y config)
        self.report_format = "pbir" if "$schema" in data else "legacy"
        print(f"   Formato detectado: {self.report_format.upper()}")
        
        self.schema = data.get("$schema")
        self.themeCollection = data.get("themeCollection")
        self.filterConfig = data.get("filterConfig", {})
        
        # En legacy, los filtros de reporte están en la clave "filters" (puede ser JSON string)
        if self.report_format == "legacy" and not self.filterConfig:
            raw_filters = data.get("filters", [])
            if isinstance(raw_filters, str):
                try:
                    raw_filters = json.loads(raw_filters)
                except json.JSONDecodeError:
                    raw_filters = []
            if isinstance(raw_filters, list) and raw_filters:
                self.filterConfig = {"filters": raw_filters}
        
        self.objects = data.get("objects")
        self.publicCustomVisuals = data.get("publicCustomVisuals")
        self.resourcePackages = data.get("resourcePackages")
        self.settings = data.get("settings")
        self.slowDataSourceSettings = data.get("slowDataSourceSettings")
        
        # Almacenar los datos crudos para formato antiguo
        self._report_data = data
        
        self.allfilter_descriptions = self.extract_filter_descriptions(self.filterConfig)
        self.filters = Filter.extract_from_config(
            self.filterConfig,
            filter_type="report"
        )

    def _load_pages(self):
        """Carga las páginas del informe desde la carpeta 'pages' (PBIR) o desde 'sections' (legacy)."""
        
        if self.report_format == "legacy":
            self._load_legacy_pages()
        elif self.pages_path and os.path.isdir(self.pages_path):
            self._load_pbir_pages()
        else:
            print(f"⚠️ No se encontraron páginas (format={self.report_format}, pages_path={self.pages_path})")
    
    def _load_pbir_pages(self):
        """Carga las páginas en formato PBIR desde la carpeta 'pages'."""
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
    
    def _load_legacy_pages(self):
        """Carga las páginas en formato legacy desde el array 'sections' del report.json."""
        if not self._report_data:
            return
        
        sections = self._report_data.get('sections', [])
        for idx, section in enumerate(sections):
            try:
                # Crear un objeto Page simulado desde cada section
                page = self._create_page_from_legacy_section(section, idx)
                if page:
                    self.pages.append(page)
                    # Agregar el ID de la página al pageOrder
                    if 'name' in section:
                        self.pageOrder.append(section['name'])
            except Exception as e:
                print(f"Error al procesar legacy section {idx}: {e}")
        
        # Establecer la primera página como activa si no hay información
        if self.pages and not self.activePageName:
            self.activePageName = self.pages[0].name if hasattr(self.pages[0], 'name') else 'Page 1'
    
    def _create_page_from_legacy_section(self, section: dict, section_index: int) -> Optional['Page']:
        """Crea un objeto Page a partir de una section del formato legacy."""
        try:
            # Extraer información básica de la section
            page_name = section.get('name', f'Page {section_index + 1}')
            display_name = section.get('displayName', page_name)
            # Crear un directorio temporal para almacenar los datos de la página
            # Usar pages_path si existe, sino usar el root_path
            base_dir = self.pages_path if self.pages_path else self.root_path
            temp_page_dir = os.path.join(base_dir, f'_legacy_{section_index}')

            # Crear el directorio si no existe
            os.makedirs(temp_page_dir, exist_ok=True)

            # Crear el subdirectorio 'visuals' para almacenar los visuals
            visuals_dir = os.path.join(temp_page_dir, 'visuals')
            os.makedirs(visuals_dir, exist_ok=True)

            # Extraer visualContainers y crear archivos visual.json individuales
            visual_containers = section.get('visualContainers', [])
            for visual_idx, visual_container in enumerate(visual_containers):
                # Extraer el config del visual
                visual_config = visual_container.get('config', '{}')

                # Si config es un string JSON, parsearlo
                if isinstance(visual_config, str):
                    try:
                        visual_data = json.loads(visual_config)
                    except json.JSONDecodeError:
                        print(f"⚠️  No se pudo parsear visual config como JSON en visual {visual_idx}")
                        visual_data = {}
                else:
                    visual_data = visual_config
                
                # En formato legacy, la posición está en el visualContainer, no dentro del config
                # Inyectar position para que Visual.__init__ la encuentre
                if 'position' not in visual_data:
                    visual_data['position'] = {
                        "x": visual_container.get('x', 0),
                        "y": visual_container.get('y', 0),
                        "width": visual_container.get('width', 100),
                        "height": visual_container.get('height', 100),
                        "z": visual_container.get('z', 0),
                        "tabOrder": visual_container.get('tabOrder', 0),
                    }
                # Buscar mapeo de alias a entidad real en prototypeQuery.From
                alias_map = {}
                proto_query = visual_data.get('prototypeQuery')
                if not proto_query:
                    sv= visual_data.get("singleVisual")
                    if sv and isinstance(sv, dict):
                        proto_query = sv.get('prototypeQuery')
                if proto_query and isinstance(proto_query, dict):
                    from_list = proto_query.get('From')
                    if isinstance(from_list, list):
                        for entry in from_list:
                            if isinstance(entry, dict) and 'Name' in entry and 'Entity' in entry:
                                alias_map[entry['Name']] = entry['Entity']
                
                def sustituir_source_ref(obj):
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            # Solo sustituir en SourceRef
                            if k == 'SourceRef' and isinstance(v, dict):
                                # Sustituir solo en Source y Entity
                                if 'Source' in v and v['Source'] in alias_map:
                                    v['Source'] = alias_map[v['Source']]
                                if 'Entity' in v and v['Entity'] in alias_map:
                                    v['Entity'] = alias_map[v['Entity']]
                            else:
                                sustituir_source_ref(v)
                    elif isinstance(obj, list):
                        for item in obj:
                            sustituir_source_ref(item)

                sustituir_source_ref(visual_data)

                # En legacy, los filtros del visual están en visualContainer.filters (JSON string separado del config)
                visual_raw_filters = visual_container.get('filters', '[]')
                if isinstance(visual_raw_filters, str):
                    try:
                        visual_raw_filters = json.loads(visual_raw_filters)
                    except json.JSONDecodeError:
                        visual_raw_filters = []
                if isinstance(visual_raw_filters, list) and visual_raw_filters:
                    visual_data['filterConfig'] = {"filters": visual_raw_filters}

                # Obtener el nombre del visual o usar un nombre por defecto
                visual_name = visual_data.get('name', f'visual_{visual_idx}')

                # Crear subdirectorio para este visual
                visual_dir = os.path.join(visuals_dir, visual_name)
                os.makedirs(visual_dir, exist_ok=True)

                # Guardar el visual.json
                visual_json_path = os.path.join(visual_dir, 'visual.json')
                with open(visual_json_path, 'w', encoding='utf-8') as f:
                    json.dump(visual_data, f, indent=2)
            
            # Crear el page.json (sin visualContainers, ya que ahora están en archivos separados)
            # En legacy, 'filters' puede ser un string JSON; parsearlo y convertirlo al formato filterConfig
            raw_filters = section.get('filters', [])
            if isinstance(raw_filters, str):
                try:
                    raw_filters = json.loads(raw_filters)
                except json.JSONDecodeError:
                    raw_filters = []
            # Convertir al formato que Page espera: filterConfig = {"filters": [...]}
            filter_config = {"filters": raw_filters} if isinstance(raw_filters, list) and raw_filters else {}
            
            # Extraer visibility desde el config de la section (es un string JSON en legacy)
            page_visibility = section.get('visibility')
            if page_visibility is None:
                raw_config = section.get('config', '{}')
                if isinstance(raw_config, str):
                    try:
                        config_parsed = json.loads(raw_config)
                        page_visibility = config_parsed.get('visibility')
                    except json.JSONDecodeError:
                        pass
            
            page_data = {
                'name': page_name,
                'displayName': display_name,
                'filterConfig': filter_config,
                'visibility': page_visibility,
                'height': section.get('height'),
                'width': section.get('width')
            }
            
            # Guardar el page.json temporal
            page_json_path = os.path.join(temp_page_dir, 'page.json')
            with open(page_json_path, 'w', encoding='utf-8') as f:
                json.dump(page_data, f, indent=2)
            
            # Crear el objeto Page desde el directorio
            page = Page(temp_page_dir)
            return page
            
        except Exception as e:
            print(f"Error al crear Page desde legacy section: {e}")
            import traceback
            traceback.print_exc()
            return None

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

    def _infer_workspace_and_report_id(self, connection):
        """
        Intenta inferir workspace_id y report_id desde la base de datos usando los nombres del path.
        
        Path ejemplo: "D:\\mcpdata\\toyota\\TES - CONCESIONARIOS\\TES - Gestión Comercial.Report"
        - Workspace name: "TES - CONCESIONARIOS" (carpeta padre del .Report)
        - Report name: "TES - Gestión Comercial" (basename sin .Report)
        
        Args:
            connection: Conexión DuckDB
        """
        try:
            # Extraer workspace name del path (carpeta padre del .Report)
            parent_path = os.path.dirname(self.root_path)
            workspace_name = os.path.basename(parent_path)
            
            # Extraer report name del path (basename sin .Report)
            basename = os.path.basename(self.root_path)
            report_name = basename.replace('.Report', '')
            
            # Intentar buscar workspace_id si es nulo
            if not self.workspace_id and workspace_name:
                try:
                    # Verificar que la tabla workspace existe
                    tables = connection.execute("SHOW TABLES").fetchall()
                    table_names = [t[0] for t in tables]
                    
                    if 'workspace' in table_names:
                        result = connection.execute(
                            "SELECT id FROM workspace WHERE name = ?", 
                            [workspace_name]
                        ).fetchone()
                        
                        if result:
                            self.workspace_id = result[0]
                            print(f"[INFO] Workspace ID inferido: {self.workspace_id} ('{workspace_name}')")
                except Exception as e:
                    # No hay problema si falla, puede ser la primera vez
                    pass
            
            # Intentar buscar report_id si es nulo
            if not self.report_id and report_name:
                try:
                    # Verificar que la tabla report existe
                    tables = connection.execute("SHOW TABLES").fetchall()
                    table_names = [t[0] for t in tables]
                    
                    if 'report' in table_names:
                        # Buscar por nombre y workspace_id si lo tenemos
                        if self.workspace_id:
                            result = connection.execute(
                                "SELECT report_id FROM report WHERE name = ? AND workspace_id = ?", 
                                [report_name, self.workspace_id]
                            ).fetchone()
                        else:
                            # Buscar solo por nombre si no tenemos workspace_id
                            result = connection.execute(
                                "SELECT report_id FROM report WHERE name = ?", 
                                [report_name]
                            ).fetchone()
                        
                        if result:
                            self.report_id = result[0]
                            print(f"[INFO] Report ID inferido: {self.report_id} ('{report_name}')")
                except Exception as e:
                    # No hay problema si falla, puede ser la primera vez
                    pass
                    
        except Exception as e:
            # Si algo falla en todo el proceso, no importa
            pass

    def save_to_database(self, connection):
        """
        Guarda el reporte en DuckDB.
        
        Args:
            connection: Conexión DuckDB (duckdb.DuckDBPyConnection)
        """
        # Intentar inferir workspace_id y report_id desde la base de datos si son nulos
        self._infer_workspace_and_report_id(connection)
        
        # Obtener nombre del reporte: usar el pasado en constructor > SemanticModel > nombre carpeta
        report_name = self.report_name  or os.path.basename(self.root_path) or self.SemanticModel
        if not report_name:
            report_name = "unknown_report"
        
        # Crear secuencias si no existen
        connection.execute("CREATE SEQUENCE IF NOT EXISTS seq_report_id START 1")
        connection.execute("CREATE SEQUENCE IF NOT EXISTS seq_report_page_id START 1")
        connection.execute("CREATE SEQUENCE IF NOT EXISTS seq_report_visual_id START 1")
        connection.execute("CREATE SEQUENCE IF NOT EXISTS seq_report_column_id START 1")
        connection.execute("CREATE SEQUENCE IF NOT EXISTS seq_report_measure_id START 1")
        
        # Crear tabla report (sin dropear, para acumular múltiples reportes)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS report (
                id INTEGER PRIMARY KEY DEFAULT nextval('seq_report_id'),
                name VARCHAR NOT NULL,
                report_id VARCHAR,
                workspace_id VARCHAR,
                semantic_model_reference VARCHAR,
                schema VARCHAR,
                active_page_name VARCHAR,
                theme_collection JSON,
                filter_config JSON,
                created_at TIMESTAMP DEFAULT now(),
                updated_at TIMESTAMP DEFAULT now()
            )
        """)
        
        # Buscar si el reporte ya existe (por report_id o por nombre)
        report_id = None
        if self.report_id:
            report_id_result = connection.execute("SELECT id FROM report WHERE report_id = ?", [self.report_id]).fetchall()
            report_id = report_id_result[0][0] if report_id_result else None
        if not report_id:
            report_id_result = connection.execute("SELECT id FROM report WHERE name = ?", [report_name]).fetchall()
            report_id = report_id_result[0][0] if report_id_result else None
        
        if report_id:
            # Ya existe: actualizar el registro principal
            connection.execute("""
                UPDATE report SET name = ?, report_id = ?, workspace_id = ?, semantic_model_reference = ?, 
                       schema = ?, active_page_name = ?, theme_collection = ?, filter_config = ?, updated_at = now()
                WHERE id = ?
            """, [
                report_name,
                self.report_id,
                self.workspace_id,
                self.semantic_model_id,
                self.schema,
                self.activePageName,
                json.dumps(self.themeCollection) if self.themeCollection else None,
                json.dumps(self.filterConfig) if self.filterConfig else None,
                report_id
            ])
        else:
            # No existe: insertar nuevo
            connection.execute("""
                INSERT INTO report (name, report_id, workspace_id, semantic_model_reference, schema, active_page_name, theme_collection, filter_config)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                report_name,
                self.report_id,
                self.workspace_id,
                self.semantic_model_id,
                self.schema,
                self.activePageName,
                json.dumps(self.themeCollection) if self.themeCollection else None,
                json.dumps(self.filterConfig) if self.filterConfig else None
            ])
            # Obtener el ID del registro recién insertado
            if self.report_id:
                report_id_result = connection.execute("SELECT id FROM report WHERE report_id = ?", [self.report_id]).fetchall()
                report_id = report_id_result[0][0] if report_id_result else None
            if not report_id:
                report_id_result = connection.execute("SELECT id FROM report WHERE name = ?", [report_name]).fetchall()
                report_id = report_id_result[0][0] if report_id_result else None
        
        if not report_id:
            print(f"⚠️ No se pudo obtener el ID del reporte {report_name}")
            return
        
        # CREAR TODAS LAS TABLAS PRIMERO (antes de hacer DELETEs)
        
        # Crear tabla report_page (drop y recrear para incluir visibility)
        #connection.execute("DROP TABLE IF EXISTS report_page")
        connection.execute("""
            CREATE TABLE IF NOT EXISTS report_page (
                id INTEGER PRIMARY KEY DEFAULT nextval('seq_report_page_id'),
                report_name VARCHAR NOT NULL,
                name VARCHAR NOT NULL,
                display_name VARCHAR,
                height INTEGER,
                width INTEGER,
                display_option VARCHAR,
                is_visible BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT now()
            )
        """)
        
        # Crear tabla report_visual (UNA SOLA VEZ, antes de insertar datos)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS report_visual (
                id INTEGER PRIMARY KEY DEFAULT nextval('seq_report_visual_id'),
                report_id INTEGER NOT NULL,
                page_name VARCHAR NOT NULL,
                report_name VARCHAR NOT NULL,
                name VARCHAR NOT NULL,
                visual_type VARCHAR,
                position_x FLOAT,
                position_y FLOAT,
                position_width FLOAT,
                position_height FLOAT,
                text_content TEXT,
                navigation_target VARCHAR,
                created_at TIMESTAMP DEFAULT now(),
                FOREIGN KEY(report_id) REFERENCES report(id)
            )
        """)
        
        # Crear tabla report_column_used
        connection.execute("""
            CREATE TABLE IF NOT EXISTS report_column_used (
                id INTEGER PRIMARY KEY DEFAULT nextval('seq_report_column_id'),
                report_id INTEGER NOT NULL,
                page_name VARCHAR NOT NULL,
                visual_name VARCHAR NOT NULL,
                table_name VARCHAR NOT NULL,
                column_name VARCHAR NOT NULL,
                usage_count INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT now(),
                FOREIGN KEY(report_id) REFERENCES report(id)
            )
        """)
        
        # Crear tabla report_measure_used
        connection.execute("""
            CREATE TABLE IF NOT EXISTS report_measure_used (
                id INTEGER PRIMARY KEY DEFAULT nextval('seq_report_measure_id'),
                report_id INTEGER NOT NULL,
                page_name VARCHAR NOT NULL,
                visual_name VARCHAR NOT NULL,
                table_name VARCHAR NOT NULL,
                measure_name VARCHAR NOT NULL,
                usage_count INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT now(),
                FOREIGN KEY(report_id) REFERENCES report(id)
            )
        """)
        
        # Crear secuencias para filtros
        connection.execute("CREATE SEQUENCE IF NOT EXISTS seq_report_filter_id START 1")
        connection.execute("CREATE SEQUENCE IF NOT EXISTS seq_report_page_filter_id START 1")
        connection.execute("CREATE SEQUENCE IF NOT EXISTS seq_report_visual_filter_id START 1")
        
        # Crear tabla report_filter (filtros a nivel de reporte)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS report_filter (
                id INTEGER PRIMARY KEY DEFAULT nextval('seq_report_filter_id'),
                report_id INTEGER NOT NULL,
                filter_name VARCHAR NOT NULL,
                table_name VARCHAR NOT NULL,
                column_name VARCHAR NOT NULL,
                filter_description TEXT,
                created_at TIMESTAMP DEFAULT now(),
                FOREIGN KEY(report_id) REFERENCES report(id)
            )
        """)
        
        # Crear tabla report_page_filter (filtros a nivel de página)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS report_page_filter (
                id INTEGER PRIMARY KEY DEFAULT nextval('seq_report_page_filter_id'),
                report_id INTEGER NOT NULL,
                page_name VARCHAR NOT NULL,
                filter_name VARCHAR NOT NULL,
                table_name VARCHAR NOT NULL,
                column_name VARCHAR NOT NULL,
                filter_description TEXT,
                created_at TIMESTAMP DEFAULT now(),
                FOREIGN KEY(report_id) REFERENCES report(id)
            )
        """)
        
        # Crear tabla report_visual_filter (filtros a nivel de visual)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS report_visual_filter (
                id INTEGER PRIMARY KEY DEFAULT nextval('seq_report_visual_filter_id'),
                report_id INTEGER NOT NULL,
                page_name VARCHAR NOT NULL,
                visual_name VARCHAR NOT NULL,
                filter_name VARCHAR NOT NULL,
                table_name VARCHAR NOT NULL,
                column_name VARCHAR NOT NULL,
                filter_description TEXT,
                created_at TIMESTAMP DEFAULT now(),
                FOREIGN KEY(report_id) REFERENCES report(id)
            )
        """)
        
        # AHORA SÍ: Limpiar datos antiguos de este reporte (sin dropear las tablas completas)
        connection.execute("DELETE FROM report_measure_used WHERE report_id = ?", [report_id])
        connection.execute("DELETE FROM report_column_used WHERE report_id = ?", [report_id])
        connection.execute("DELETE FROM report_visual WHERE report_id = ?", [report_id])
        connection.execute("DELETE FROM report_page WHERE report_name = ?", [report_name])
        connection.execute("DELETE FROM report_filter WHERE report_id = ?", [report_id])
        connection.execute("DELETE FROM report_page_filter WHERE report_id = ?", [report_id])
        connection.execute("DELETE FROM report_visual_filter WHERE report_id = ?", [report_id])
        
        # Insertar páginas e visuals
        for page in self.pages:
            # visibility=1 significa oculta en Power BI, 0 o None = visible
            is_visible = not (page.visibility == 1)
            connection.execute("""
                INSERT INTO report_page (report_name, name, display_name, height, width, display_option, is_visible)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [
                report_name,
                page.name,
                page.displayName,
                page.height,
                page.width,
                page.displayOption,
                is_visible
            ])
            
            # Insertar visuals de la página
            for visual in page.visuals:
                connection.execute("""
                    INSERT INTO report_visual (report_id, page_name, report_name, name, visual_type, position_x, position_y, position_width, position_height, text_content, navigation_target)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    report_id,
                    page.name,
                    report_name,
                    visual.name,
                    visual.visualType,
                    visual.position.get('x'),
                    visual.position.get('y'),
                    visual.position.get('width'),
                    visual.position.get('height'),
                    visual.text,
                    visual.navigationTarget
                ])
        
        # Insertar columnas usadas (con relación a report_visual)
        columns_used = self.get_all_columns_used()
        
        # Insertar columnas usadas por cada visual
        for page in self.pages:
            for visual in page.visuals:
                # Agrupar columnas usadas en este visual
                visual_columns = {}
                for col_ref in visual.columns_used:
                    if '.' in col_ref:
                        parts = col_ref.split('.')
                        table = parts[0]
                        col = '.'.join(parts[1:])
                        key = (table, col)
                        visual_columns[key] = visual_columns.get(key, 0) + 1
                
                # Insertar cada columna con su contador
                for (table, col), count in visual_columns.items():
                    connection.execute("""
                        INSERT INTO report_column_used (report_id, page_name, visual_name, table_name, column_name, usage_count)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, [report_id, page.name, visual.name, table, col, count])
        
        # Insertar medidas usadas (con relación a report_visual)
        measures_used = self.get_all_measures_used()
        
        # Insertar medidas usadas por cada visual
        for page in self.pages:
            for visual in page.visuals:
                # Agrupar medidas usadas en este visual
                visual_measures = {}
                for measure_ref in visual.measures_used:
                    if '.' in measure_ref:
                        parts = measure_ref.split('.')
                        table = parts[0]
                        measure = '.'.join(parts[1:])
                        key = (table, measure)
                        visual_measures[key] = visual_measures.get(key, 0) + 1
                
                # Insertar cada medida con su contador
                for (table, measure), count in visual_measures.items():
                    connection.execute("""
                        INSERT INTO report_measure_used (report_id, page_name, visual_name, table_name, measure_name, usage_count)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, [report_id, page.name, visual.name, table, measure, count])
        
        # Insertar filtros a nivel de REPORTE
        for filter_obj in self.filters:
            connection.execute("""
                INSERT INTO report_filter (report_id, filter_name, table_name, column_name, filter_description)
                VALUES (?, ?, ?, ?, ?)
            """, [
                report_id,
                filter_obj.name,
                filter_obj.table_name,
                filter_obj.column_name,
                filter_obj.description
            ])
        
        # Insertar filtros a nivel de PÁGINA y VISUAL
        for page in self.pages:
            # Filtros a nivel de página
            for filter_obj in page.filters:
                connection.execute("""
                    INSERT INTO report_page_filter (report_id, page_name, filter_name, table_name, column_name, filter_description)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, [
                    report_id,
                    page.name,
                    filter_obj.name,
                    filter_obj.table_name,
                    filter_obj.column_name,
                    filter_obj.description
                ])
            
            # Filtros a nivel de visual
            for visual in page.visuals:
                for filter_obj in visual.filters:
                    connection.execute("""
                        INSERT INTO report_visual_filter (report_id, page_name, visual_name, filter_name, table_name, column_name, filter_description)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, [
                        report_id,
                        page.name,
                        visual.name,
                        filter_obj.name,
                        filter_obj.table_name,
                        filter_obj.column_name,
                        filter_obj.description
                    ])

    def __repr__(self):
        return f"clsReport(model={self.SemanticModel}, model_id={self.semantic_model_id}, pages={len(self.pages)})"
