from pathlib import Path
from typing import List, Optional, Dict, Any, Set, Literal
from .tmdl_parser import TmdlParser
import re 

class Column:
    """Representa una columna de una tabla"""
    
    def __init__(self):
        self.name: str = ""
        self.data_type: Optional[str] = None
        self.source_column: Optional[str] = None
        self.format_string: Optional[str] = None
        self.summarize_by: Optional[str] = None
        self.is_hidden: bool = False
        self.raw_content: str = ""

class Measure:
    """Representa una medida DAX"""
    
    def __init__(self):
        self.name: str = ""
        self.expression: str = ""
        self.format_string: Optional[str] = None
        self.is_hidden: bool = False
        self.raw_content: str = ""

class Partition:
    """Representa una partición de tabla"""
    
    def __init__(self):
        self.name: str = ""
        self.mode: Optional[str] = None  # import, directQuery, dual
        self.source_type: Optional[str] = None  # m, calculated, etc.
        self.source_expression: str = ""  # Código M, SQL, o expresión DAX
        self.raw_content: str = ""

class Table:
    """
    Representa una tabla completa con sus columnas, medidas y particiones.
    """
    
    def __init__(self):
        self.name: str = ""
        self.columns: List[Column] = []
        self.measures: List[Measure] = []
        self.partitions: List[Partition] = []
        self.hierarchies: List[Dict] = []
        self.is_hidden: bool = False
        self.line_age_granularity: Optional[str] = None
        self.annotations: Dict[str, Any] = {}
        self.raw_content: str = ""
        
    @classmethod
    def from_file(cls, filepath: Path) -> 'Table':
        """Carga una tabla desde un archivo .tmdl"""
        instance = cls()
        instance.name = filepath.stem
        
        with open(filepath, 'r', encoding='utf-8') as f:
            instance.raw_content = f.read()
        
        parser = TmdlParser(instance.raw_content)
        instance.is_hidden = parser.get_property('isHidden', False)
        instance.line_age_granularity = parser.get_property('lineageGranularity')
        instance.annotations = parser.get_annotations()
        
        # Parsear columnas embebidas en el archivo
        instance.columns = cls._parse_columns(instance.raw_content)
        
        # Parsear medidas embebidas
        instance.measures = cls._parse_measures(instance.raw_content)
        
        # Parsear particiones embebidas
        instance.partitions = cls._parse_partitions(instance.raw_content)
        
        return instance
    
    @staticmethod
    def _parse_columns(content: str) -> List[Column]:
        """Parsea las columnas del contenido TMDL"""
        columns = []
        in_column = False
        current_column = None
        column_content = []
        
        for line in content.split('\n'):
            if line.strip().startswith('column '):
                if current_column:
                    current_column.raw_content = '\n'.join(column_content)
                    columns.append(current_column)
                
                current_column = Column()
                # Extraer nombre de la columna
                match = re.match(r".*column\s+['\"]?([^'\"]+)['\"]?", line)
                if match:
                    current_column.name = match.group(1)
                column_content = [line]
                in_column = True
            elif in_column:
                column_content.append(line)
                if line.strip() and not line.strip().startswith((' ', '\t')):
                    if current_column:
                        current_column.raw_content = '\n'.join(column_content)
                        parser = TmdlParser(current_column.raw_content)
                        current_column.data_type = parser.get_property('dataType')
                        current_column.source_column = parser.get_property('sourceColumn')
                        current_column.format_string = parser.get_property('formatString')
                        current_column.summarize_by = parser.get_property('summarizeBy')
                        current_column.is_hidden = parser.get_property('isHidden', False)
                        columns.append(current_column)
                    in_column = False
                    current_column = None
                    column_content = []
        
        if current_column:
            current_column.raw_content = '\n'.join(column_content)
            columns.append(current_column)
        
        return columns
    
    @staticmethod
    def _parse_measures(content: str) -> List[Measure]:
        """Parsea las medidas del contenido TMDL, soportando expresiones multi-línea y bloques con ```."""
        measures = []
        lines = content.split('\n')

        in_measure = False
        in_code_block = False
        current_measure = None
        measure_content = []
        base_indent = 0

        for line in lines:
            # Detectar inicio de una medida
            if re.match(r"^\s*measure\s+", line):
                # Cerrar medida previa
                if current_measure:
                    current_measure.raw_content = '\n'.join(measure_content)
                    parser = TmdlParser(current_measure.raw_content)
                    current_measure.format_string = parser.get_property('formatString')
                    current_measure.is_hidden = parser.get_property('isHidden', False)
                    measures.append(current_measure)

                current_measure = Measure()
                measure_content = [line]
                in_measure = True
                in_code_block = False
                base_indent = len(line) - len(line.lstrip())

                # Nombre de la medida
                match = re.match(r"^\s*measure\s+['\"]?([^'\"=]+)['\"]?\s*=", line)
                if match:
                    current_measure.name = match.group(1).strip()

                # Expresión en la misma línea (si existe)
                expr_match = re.match(r"^\s*measure\s+['\"]?[^'\"=]+['\"]?\s*=\s*(.+)", line)
                if expr_match:
                    expr_line = expr_match.group(1).strip()
                    # Si empieza bloque ``` quitarlo y activar modo bloque
                    if expr_line.startswith('```'):
                        in_code_block = True
                        expr_line = expr_line[3:].strip()
                    if expr_line:
                        current_measure.expression = expr_line
                else:
                    current_measure.expression = ""
                continue

            if in_measure:
                measure_content.append(line)

                # Toggle de bloque de código
                stripped = line.strip()
                if stripped.startswith('```'):
                    # Si ya estamos en bloque, cerrar; si no, abrir
                    if in_code_block:
                        in_code_block = False
                    else:
                        in_code_block = True
                    # Quitar las ``` de la expresión (solo marcadores, no contenido)
                    marker = stripped[3:].strip()
                    if marker:
                        current_measure.expression += ("\n" if current_measure.expression else "") + marker
                    continue

                # Si estamos dentro de bloque de código, toda línea pertenece a la expresión
                if in_code_block:
                    current_measure.expression += ("\n" if current_measure.expression else "") + line.rstrip()
                    continue

                # Fuera de bloque: detectar propiedades o fin de medida
                # Propiedades comunes de medida
                if re.match(r"^\s*formatString\s*:", line):
                    # Se capturará luego via TmdlParser; no añadir a expresión
                    pass
                elif re.match(r"^\s*isHidden\b", line):
                    pass
                elif re.match(r"^\s*annotation\s+", line):
                    # Anotaciones no forman parte de la expresión
                    pass
                else:
                    # Si es una línea indented (más que la base), considerarla parte de la expresión
                    current_indent = len(line) - len(line.lstrip())
                    if stripped and current_indent > base_indent:
                        current_measure.expression += ("\n" if current_measure.expression else "") + stripped
                    else:
                        # Fin del bloque de medida cuando volvemos a indentación base y la línea no es vacía
                        if stripped:
                            current_measure.raw_content = '\n'.join(measure_content)
                            parser = TmdlParser(current_measure.raw_content)
                            current_measure.format_string = parser.get_property('formatString')
                            current_measure.is_hidden = parser.get_property('isHidden', False)
                            measures.append(current_measure)
                            # Reset estado para procesar esta línea como fuera de medida
                            in_measure = False
                            in_code_block = False
                            current_measure = None
                            measure_content = []
                            # Continuar para re-evaluar la línea en el siguiente ciclo
                            continue
                
                # Continuar a siguiente línea
                continue

        # Cerrar última medida
        if current_measure:
            current_measure.raw_content = '\n'.join(measure_content)
            parser = TmdlParser(current_measure.raw_content)
            current_measure.format_string = parser.get_property('formatString')
            current_measure.is_hidden = parser.get_property('isHidden', False)
            measures.append(current_measure)

        return measures
    
    @staticmethod
    def _parse_partitions(content: str) -> List[Partition]:
        """Parsea las particiones del contenido TMDL"""
        partitions = []
        in_partition = False
        current_partition = None
        partition_content = []
        in_source_block = False
        base_indent = 0
        
        for line in content.split('\n'):
            stripped = line.strip()
            
            # Detectar inicio de partición: "partition NombreParticion = tipo"
            if re.match(r'^\s*partition\s+', line):
                # Guardar partición anterior si existe
                if current_partition:
                    current_partition.raw_content = '\n'.join(partition_content)
                    partitions.append(current_partition)
                
                current_partition = Partition()
                partition_content = [line]
                in_partition = True
                in_source_block = False
                base_indent = len(line) - len(line.lstrip())
                
                # Extraer nombre y tipo: "partition DimCustomer = m"
                match = re.match(r'^\s*partition\s+([^\s=]+)\s*=\s*(\w+)', line)
                if match:
                    current_partition.name = match.group(1)
                    current_partition.source_type = match.group(2)  # m, calculated, etc.
                continue
            
            if in_partition:
                partition_content.append(line)
                current_indent = len(line) - len(line.lstrip())
                
                # Detectar "mode: import/directQuery/dual"
                if re.match(r'^\s*mode:\s*', line):
                    mode_match = re.match(r'^\s*mode:\s*(\w+)', line)
                    if mode_match:
                        current_partition.mode = mode_match.group(1)
                    continue
                
                # Detectar inicio de bloque source
                if re.match(r'^\s*source\s*=', line):
                    in_source_block = True
                    # Capturar expresión inline si existe
                    source_match = re.match(r'^\s*source\s*=\s*(.+)', line)
                    if source_match:
                        expr = source_match.group(1).strip()
                        current_partition.source_expression = expr
                    continue
                
                # Si estamos en bloque source, capturar contenido
                if in_source_block:
                    # Líneas con indentación mayor al base son parte del source
                    if stripped and current_indent > base_indent:
                        if current_partition.source_expression:
                            current_partition.source_expression += "\n" + line.strip()
                        else:
                            current_partition.source_expression = line.strip()
                    elif stripped:
                        # Fin del bloque source (volvemos a indentación base)
                        in_source_block = False
                        # Si la línea no es otra propiedad de partition, terminamos
                        if not re.match(r'^\s*(mode|annotation|dataView):', line):
                            in_partition = False
                            continue
        
        # Guardar última partición
        if current_partition:
            current_partition.raw_content = '\n'.join(partition_content)
            partitions.append(current_partition)
        
        return partitions
    
    def save_to_file(self, filepath: Path):
        """Guarda la tabla a un archivo .tmdl"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.raw_content)
    
    def filter_elements(
        self,
        columns: Optional[List[str]] = None,
        measures: Optional[List[str]] = None,
        hierarchies: Optional[List[str]] = None,
        mode: Literal['include', 'exclude'] = 'include'
    ) -> 'Table':
        """
        Crea una copia de la tabla con elementos filtrados.
        
        Args:
            columns: Lista de nombres de columnas
            measures: Lista de nombres de medidas
            hierarchies: Lista de nombres de jerarquías
            mode: 'include' para mantener solo los especificados, 
                  'exclude' para eliminar los especificados
        
        Returns:
            Nueva instancia de Table con elementos filtrados
        """
        filtered_table = Table()
        filtered_table.name = self.name
        filtered_table.is_hidden = self.is_hidden
        filtered_table.line_age_granularity = self.line_age_granularity
        filtered_table.annotations = self.annotations.copy()
        
        # IMPORTANTE: Las particiones SIEMPRE se mantienen (son obligatorias)
        filtered_table.partitions = self.partitions.copy()
        
        # Filtrar columnas
        if columns is not None:
            columns_set = set(columns)
            if mode == 'include':
                filtered_table.columns = [
                    col for col in self.columns 
                    if col.name in columns_set
                ]
            else:  # exclude
                filtered_table.columns = [
                    col for col in self.columns 
                    if col.name not in columns_set
                ]
        else:
            filtered_table.columns = self.columns.copy()
        
        # Filtrar medidas
        if measures is not None:
            measures_set = set(measures)
            if mode == 'include':
                filtered_table.measures = [
                    measure for measure in self.measures 
                    if measure.name in measures_set
                ]
            else:  # exclude
                filtered_table.measures = [
                    measure for measure in self.measures 
                    if measure.name not in measures_set
                ]
        else:
            filtered_table.measures = self.measures.copy()
        
        # Filtrar jerarquías
        if hierarchies is not None:
            hierarchies_set = set(hierarchies)
            if mode == 'include':
                filtered_table.hierarchies = [
                    hierarchy for hierarchy in self.hierarchies 
                    if hierarchy.get('name') in hierarchies_set
                ]
            else:  # exclude
                filtered_table.hierarchies = [
                    hierarchy for hierarchy in self.hierarchies 
                    if hierarchy.get('name') not in hierarchies_set
                ]
        else:
            filtered_table.hierarchies = self.hierarchies.copy()
        
        # CORREGIDO: Usar raw_content original y filtrar en lugar de reconstruir
        filtered_table.raw_content = self._filter_raw_content(
            filtered_table.columns,
            filtered_table.measures,
            filtered_table.hierarchies
        )
        
        return filtered_table
    
    def _filter_raw_content(
        self,
        filtered_columns: List[Column],
        filtered_measures: List[Measure],
        filtered_hierarchies: List[Dict]
    ) -> str:
        """
        Filtra el contenido raw manteniendo solo los elementos especificados,
        pero preservando todos sus atributos originales.
        
        Args:
            filtered_columns: Columnas a mantener
            filtered_measures: Medidas a mantener
            filtered_hierarchies: Jerarquías a mantener
        
        Returns:
            Contenido TMDL filtrado con atributos completos
        """
        lines = self.raw_content.split('\n')
        result_lines = []
        
        # Conjuntos de nombres para búsqueda rápida
        column_names = {col.name for col in filtered_columns}
        measure_names = {measure.name for measure in filtered_measures}
        hierarchy_names = {hier.get('name') for hier in filtered_hierarchies}
        
        # Variables de estado para el parser
        in_element = False
        current_element_type = None
        current_element_name = None
        current_element_lines = []
        keep_current_element = False
        base_indent = 0
        
        # Variables para detectar el nivel de tabla
        in_table_header = True
        table_base_indent = 0
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            current_indent = len(line) - len(line.lstrip())
            
            # Detectar encabezado de tabla (al inicio)
            if i == 0 or (in_table_header and stripped.startswith('table ')):
                result_lines.append(line)
                table_base_indent = current_indent
                in_table_header = True
                i += 1
                continue
            
            # Propiedades y anotaciones de nivel tabla (antes de cualquier elemento)
            if in_table_header and not in_element:
                # Si encontramos un elemento (column, measure, etc.), terminamos el header
                if stripped.startswith('column ') or stripped.startswith('measure ') or \
                   stripped.startswith('hierarchy ') or stripped.startswith('partition '):
                    in_table_header = False
                    # Procesaremos esta línea en la siguiente iteración
                else:
                    # Líneas del encabezado de tabla (lineageTag, isHidden, annotations de tabla)
                    result_lines.append(line)
                    i += 1
                    continue
            
            # Detectar inicio de columna
            if stripped.startswith('column '):
                # Guardar elemento anterior si existe y se debe mantener
                if in_element and keep_current_element:
                    result_lines.extend(current_element_lines)
                
                # Nuevo elemento
                in_element = True
                current_element_type = 'column'
                current_element_lines = [line]
                base_indent = current_indent
                
                # Extraer nombre de columna - mejorado para manejar comillas
                match = re.match(r"column\s+['\"]?([^'\"]+)['\"]?", stripped)
                if match:
                    current_element_name = match.group(1).strip("'\"")
                    keep_current_element = current_element_name in column_names
                else:
                    keep_current_element = False
                
                i += 1
                continue
            
            # Detectar inicio de medida
            elif stripped.startswith('measure '):
                # Guardar elemento anterior si existe y se debe mantener
                if in_element and keep_current_element:
                    result_lines.extend(current_element_lines)
                
                # Nuevo elemento
                in_element = True
                current_element_type = 'measure'
                current_element_lines = [line]
                base_indent = current_indent
                
                # Extraer nombre de medida (puede tener = en la misma línea)
                match = re.match(r"measure\s+['\"]?([^'\"=]+)['\"]?", stripped)
                if match:
                    current_element_name = match.group(1).strip("'\" ")
                    keep_current_element = current_element_name in measure_names
                else:
                    keep_current_element = False
                
                i += 1
                continue
            
            # Detectar inicio de jerarquía
            elif stripped.startswith('hierarchy '):
                # Guardar elemento anterior si existe y se debe mantener
                if in_element and keep_current_element:
                    result_lines.extend(current_element_lines)
                
                # Nuevo elemento
                in_element = True
                current_element_type = 'hierarchy'
                current_element_lines = [line]
                base_indent = current_indent
                
                # Extraer nombre de jerarquía
                match = re.match(r"hierarchy\s+['\"]?([^'\"]+)['\"]?", stripped)
                if match:
                    current_element_name = match.group(1).strip("'\"")
                    keep_current_element = current_element_name in hierarchy_names
                else:
                    keep_current_element = False
                
                i += 1
                continue
            
            # Detectar inicio de partition (siempre se mantienen)
            elif stripped.startswith('partition '):
                # Guardar elemento anterior si existe y se debe mantener
                if in_element and keep_current_element:
                    result_lines.extend(current_element_lines)
                
                in_element = False
                current_element_type = None
                current_element_name = None
                current_element_lines = []
                keep_current_element = False
                
                # Agregar la línea de partition
                result_lines.append(line)
                i += 1
                continue
            
            # Estamos dentro de un elemento (column, measure, hierarchy)
            if in_element:
                # Si la indentación vuelve al nivel base o menor y no es línea vacía,
                # significa fin del elemento actual
                if current_indent <= base_indent and stripped:
                    # Guardar elemento actual si se debe mantener
                    if keep_current_element:
                        result_lines.extend(current_element_lines)
                    
                    # Reset para procesar la línea actual en la siguiente iteración
                    in_element = False
                    current_element_type = None
                    current_element_name = None
                    current_element_lines = []
                    keep_current_element = False
                    continue
                else:
                    # Línea pertenece al elemento actual
                    current_element_lines.append(line)
            else:
                # Fuera de elementos específicos, agregar línea directamente
                # (partition, anotaciones globales, etc.)
                result_lines.append(line)
            
            i += 1
        
        # Guardar último elemento si existe y se debe mantener
        if in_element and keep_current_element:
            result_lines.extend(current_element_lines)
        
        return '\n'.join(result_lines)
    
    def _rebuild_raw_content(self, filtered_table: 'Table') -> str:
        """
        DEPRECATED: Usar _filter_raw_content en su lugar.
        Este método reconstruye desde cero y puede perder atributos.
        """
        lines = []
        
        # Header de la tabla
        lines.append(f"table {self.name}")
        if self.line_age_granularity:
            lines.append(f"\tlineageGranularity: {self.line_age_granularity}")
        if self.is_hidden:
            lines.append(f"\tisHidden")
        
        # Anotaciones
        for key, value in self.annotations.items():
            lines.append(f"\tannotation {key} = {value}")
        
        # Columnas filtradas
        for column in filtered_table.columns:
            lines.append("")
            lines.append(f"\tcolumn {column.name}")
            if column.data_type:
                lines.append(f"\t\tdataType: {column.data_type}")
            if column.source_column:
                lines.append(f"\t\tsourceColumn: {column.source_column}")
            if column.format_string:
                lines.append(f"\t\tformatString: {column.format_string}")
            if column.summarize_by:
                lines.append(f"\t\tsummarizeBy: {column.summarize_by}")
            if column.is_hidden:
                lines.append(f"\t\tisHidden")
        
        # Medidas filtradas
        for measure in filtered_table.measures:
            lines.append("")
            lines.append(f"\tmeasure {measure.name} =")
            lines.append(f"\t\t{measure.expression}")
            if measure.format_string:
                lines.append(f"\t\tformatString: {measure.format_string}")
            if measure.is_hidden:
                lines.append(f"\t\tisHidden")
        
        # Jerarquías filtradas
        for hierarchy in filtered_table.hierarchies:
            lines.append("")
            lines.append(f"\thierarchy {hierarchy.get('name', 'Unnamed')}")
            # Aquí se pueden agregar más detalles de jerarquías si es necesario
        
        # Particiones
        for partition in filtered_table.partitions:
            lines.append("")
            lines.append(f"\tpartition {partition.name}")
            if partition.mode:
                lines.append(f"\t\tmode: {partition.mode}")
        
        return '\n'.join(lines)
