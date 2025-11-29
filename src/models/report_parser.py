"""
ReportParser - Clase para analizar archivos .Report de Power BI y extraer referencias a tablas y columnas
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict


class ReportParser:
    """
    Analiza la estructura de archivos .Report de Power BI para extraer
    referencias a tablas y columnas utilizadas en el informe.
    """
    
    def __init__(self, report_path: str):
        """
        Inicializa el parser con la ruta al directorio .Report
        
        Args:
            report_path: Ruta al directorio .Report (ej: "FullAdventureWorks.Report")
        """
        self.report_path = Path(report_path)
        self.definition_path = self.report_path / "definition"
        self.report_json_path = self.definition_path / "report.json"
        self.pages_path = self.definition_path / "pages"
        
        # Diccionario para almacenar referencias tabla -> conjunto de columnas
        self.table_column_references: Dict[str, Set[str]] = defaultdict(set)
    
    def parse(self) -> Dict[str, List[str]]:
        """
        Analiza todo el informe y retorna un diccionario con las referencias tabla-columna
        
        Returns:
            Diccionario con estructura {tabla: [lista de columnas]}
        """
        # Reiniciar referencias
        self.table_column_references = defaultdict(set)
        
        # 1. Parsear report.json (filtros a nivel de informe)
        self._parse_report_json()
        
        # 2. Parsear cada página
        self._parse_pages()
        
        # Convertir sets a listas ordenadas para el resultado final
        return {table: sorted(list(columns)) 
                for table, columns in self.table_column_references.items()}
    
    def _parse_report_json(self):
        """Analiza el archivo report.json principal"""
        if not self.report_json_path.exists():
            return
        
        try:
            with open(self.report_json_path, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            # Extraer filtros del filterConfig
            if 'filterConfig' in report_data:
                self._extract_filters(report_data['filterConfig'])
                
        except Exception as e:
            print(f"Error al parsear report.json: {e}")
    
    def _parse_pages(self):
        """Analiza todas las páginas del informe"""
        if not self.pages_path.exists():
            return
        
        # Iterar sobre todas las carpetas de páginas
        for page_dir in self.pages_path.iterdir():
            if page_dir.is_dir():
                self._parse_page(page_dir)
    
    def _parse_page(self, page_dir: Path):
        """
        Analiza una página individual
        
        Args:
            page_dir: Ruta al directorio de la página
        """
        # 1. Parsear page.json
        page_json_path = page_dir / "page.json"
        if page_json_path.exists():
            try:
                with open(page_json_path, 'r', encoding='utf-8') as f:
                    page_data = json.load(f)
                
                # Extraer filtros de la página
                if 'filterConfig' in page_data:
                    self._extract_filters(page_data['filterConfig'])
                    
            except Exception as e:
                print(f"Error al parsear {page_json_path}: {e}")
        
        # 2. Parsear visuales
        visuals_dir = page_dir / "visuals"
        if visuals_dir.exists():
            self._parse_visuals(visuals_dir)
    
    def _parse_visuals(self, visuals_dir: Path):
        """
        Analiza todos los visuales de una página
        
        Args:
            visuals_dir: Ruta al directorio de visuales
        """
        for visual_dir in visuals_dir.iterdir():
            if visual_dir.is_dir():
                self._parse_visual(visual_dir)
    
    def _parse_visual(self, visual_dir: Path):
        """
        Analiza un visual individual
        
        Args:
            visual_dir: Ruta al directorio del visual
        """
        visual_json_path = visual_dir / "visual.json"
        if not visual_json_path.exists():
            return
        
        try:
            with open(visual_json_path, 'r', encoding='utf-8') as f:
                visual_data = json.load(f)
            
            # Extraer campos del query
            if 'visual' in visual_data and 'query' in visual_data['visual']:
                self._extract_query_fields(visual_data['visual']['query'])
            
            # Extraer filtros del visual
            if 'filterConfig' in visual_data:
                self._extract_filters(visual_data['filterConfig'])
                
        except Exception as e:
            print(f"Error al parsear {visual_json_path}: {e}")
    
    def _extract_filters(self, filter_config: dict):
        """
        Extrae referencias de tabla-columna de un filterConfig
        
        Args:
            filter_config: Diccionario con la configuración de filtros
        """
        if 'filters' not in filter_config:
            return
        
        for filter_item in filter_config['filters']:
            if 'field' not in filter_item:
                continue
            
            # Extraer tabla y columna del campo
            table, column = self._extract_field_reference(filter_item['field'])
            if table and column:
                self.table_column_references[table].add(column)
    
    def _extract_query_fields(self, query: dict):
        """
        Extrae referencias de tabla-columna de un query de visual
        
        Args:
            query: Diccionario con la query del visual
        """
        if 'queryState' not in query:
            return
        
        query_state = query['queryState']
        
        # Recorrer todas las secciones (Rows, Columns, Values, etc.)
        for section_name, section_data in query_state.items():
            if not isinstance(section_data, dict) or 'projections' not in section_data:
                continue
            
            for projection in section_data['projections']:
                if 'field' not in projection:
                    continue
                
                # Extraer tabla y columna del campo
                table, column = self._extract_field_reference(projection['field'])
                if table and column:
                    self.table_column_references[table].add(column)
    
    def _extract_field_reference(self, field: dict) -> Tuple[Optional[str], Optional[str]]:
        """
        Extrae la referencia de tabla y columna de un campo
        
        Args:
            field: Diccionario con la definición del campo
            
        Returns:
            Tupla (tabla, columna) o (None, None) si no se encuentra
        """
        # Caso 1: Campo directo (Column)
        if 'Column' in field:
            return self._extract_from_column(field['Column'])
        
        # Caso 2: Campo con agregación (Aggregation)
        if 'Aggregation' in field:
            if 'Expression' in field['Aggregation']:
                if 'Column' in field['Aggregation']['Expression']:
                    return self._extract_from_column(field['Aggregation']['Expression']['Column'])
        
        # Caso 3: Measure
        if 'Measure' in field:
            if 'Expression' in field['Measure']:
                if 'SourceRef' in field['Measure']['Expression']:
                    entity = field['Measure']['Expression']['SourceRef'].get('Entity')
                    property_name = field['Measure'].get('Property')
                    if entity and property_name:
                        return entity, property_name
        
        return None, None
    
    def _extract_from_column(self, column: dict) -> Tuple[Optional[str], Optional[str]]:
        """
        Extrae tabla y columna de una definición de columna
        
        Args:
            column: Diccionario con la definición de columna
            
        Returns:
            Tupla (tabla, columna) o (None, None)
        """
        if 'Expression' in column and 'SourceRef' in column['Expression']:
            entity = column['Expression']['SourceRef'].get('Entity')
            property_name = column.get('Property')
            
            if entity and property_name:
                return entity, property_name
        
        return None, None
    
    def get_summary(self) -> str:
        """
        Retorna un resumen legible de las referencias encontradas
        
        Returns:
            String con el resumen
        """
        if not self.table_column_references:
            return "No se encontraron referencias a tablas y columnas"
        
        lines = [f"Referencias encontradas en {self.report_path.name}:"]
        lines.append("=" * 60)
        
        for table in sorted(self.table_column_references.keys()):
            columns = sorted(self.table_column_references[table])
            lines.append(f"\n{table}:")
            for column in columns:
                lines.append(f"  - {column}")
        
        lines.append("\n" + "=" * 60)
        lines.append(f"Total: {len(self.table_column_references)} tablas, "
                    f"{sum(len(cols) for cols in self.table_column_references.values())} columnas")
        
        return "\n".join(lines)


# Función de utilidad para parsear un informe
def parse_report(report_path: str) -> Dict[str, List[str]]:
    """
    Función de conveniencia para parsear un informe
    
    Args:
        report_path: Ruta al directorio .Report
        
    Returns:
        Diccionario con estructura {tabla: [lista de columnas]}
    """
    parser = ReportParser(report_path)
    return parser.parse()


if __name__ == "__main__":
    # Ejemplo de uso
    import sys
    
    if len(sys.argv) > 1:
        report_path = sys.argv[1]
    else:
        # Usar un ejemplo por defecto
        report_path = "Modelos/FullAdventureWorks.Report"
    
    parser = ReportParser(report_path)
    references = parser.parse()
    
    print(parser.get_summary())
    print("\nDiccionario de referencias:")
    print(json.dumps(references, indent=2, ensure_ascii=False))
