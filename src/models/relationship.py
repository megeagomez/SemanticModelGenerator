from pathlib import Path
from typing import Optional, Tuple
import re
from .tmdl_parser import TmdlParser

class Relationship:
    """
    Representa una relación entre tablas en formato TMDL.
    """
    
    def __init__(self):
        self.name: Optional[str] = None
        self.from_table: Optional[str] = None
        self.from_column: Optional[str] = None
        self.to_table: Optional[str] = None
        self.to_column: Optional[str] = None
        self.cross_filtering_behavior: Optional[str] = None
        self.security_filtering_behavior: Optional[str] = None
        self.cardinality: Optional[str] = None
        self.is_active: bool = True
        self.raw_content: str = ""
    
    @staticmethod
    def _parse_table_column(combined_value: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parsea el formato combinado tabla.columna del archivo relationships.tmdl.
        
        Ejemplos:
            'Internet Sales'.'Due Date Key' -> ('Internet Sales', 'Due Date Key')
            DimCurrency.CurrencyKey -> ('DimCurrency', 'CurrencyKey')
            'Table Name'.ColumnName -> ('Table Name', 'ColumnName')
        
        Args:
            combined_value: Valor en formato tabla.columna
        
        Returns:
            Tupla (tabla, columna)
        """
        if not combined_value:
            return (None, None)
        
        # Patrón para capturar: 'tabla'.'columna' o tabla.columna o combinaciones
        # Busca tabla entre comillas simples o sin comillas, seguida de punto y columna
        pattern = r"(?:'([^']+)'|([^\s.]+))\.(?:'([^']+)'|([^\s.]+))"
        match = re.match(pattern, combined_value.strip())
        
        if match:
            # match.group(1) o match.group(2) es la tabla (con o sin comillas)
            # match.group(3) o match.group(4) es la columna (con o sin comillas)
            table = match.group(1) if match.group(1) else match.group(2)
            column = match.group(3) if match.group(3) else match.group(4)
            return (table, column)
        
        # Si no coincide el patrón, retornar None
        return (None, None)
    
    @classmethod
    def from_file(cls, filepath: Path) -> 'Relationship':
        """Carga la relación desde un archivo .tmdl"""
        instance = cls()
        instance.name = filepath.stem
        
        with open(filepath, 'r', encoding='utf-8') as f:
            instance.raw_content = f.read()
        
        parser = TmdlParser(instance.raw_content)
        
        # Parsear fromColumn (formato tabla.columna)
        from_combined = parser.get_property('fromColumn')
        instance.from_table, instance.from_column = cls._parse_table_column(from_combined)
        
        # Parsear toColumn (formato tabla.columna)
        to_combined = parser.get_property('toColumn')
        instance.to_table, instance.to_column = cls._parse_table_column(to_combined)
        
        instance.cross_filtering_behavior = parser.get_property('crossFilteringBehavior')
        instance.security_filtering_behavior = parser.get_property('securityFilteringBehavior')
        instance.cardinality = parser.get_property('cardinality')
        instance.is_active = parser.get_property('isActive', True)
        
        return instance
    
    @classmethod
    def parse_all_from_content(cls, content: str) -> list['Relationship']:
        """Parsea todas las relaciones desde un archivo relationships.tmdl"""
        relationships = []
        current_rel = None
        rel_lines = []
        in_relationship = False
        
        for line in content.split('\n'):
            stripped = line.strip()
            
            # Detectar inicio de una relación
            if stripped.startswith('relationship '):
                if current_rel and rel_lines:
                    # Guardar la relación anterior
                    current_rel.raw_content = '\n'.join(rel_lines)
                    cls._parse_relationship_properties(current_rel)
                    relationships.append(current_rel)
                
                # Nueva relación
                current_rel = cls()
                # Extraer nombre de la relación
                match = re.match(r"relationship\s+(.+)", stripped)
                if match:
                    current_rel.name = match.group(1).strip()
                else:
                    current_rel.name = f"relationship_{len(relationships)}"
                
                rel_lines = [line]
                in_relationship = True
            elif in_relationship:
                rel_lines.append(line)
        
        # Guardar la última relación
        if current_rel and rel_lines:
            current_rel.raw_content = '\n'.join(rel_lines)
            cls._parse_relationship_properties(current_rel)
            relationships.append(current_rel)
        
        return relationships
    
    @staticmethod
    def _parse_relationship_properties(relationship: 'Relationship'):
        """Parsea las propiedades de una relación desde su contenido"""
        parser = TmdlParser(relationship.raw_content)
        
        # Parsear fromColumn (formato tabla.columna)
        from_combined = parser.get_property('fromColumn')
        relationship.from_table, relationship.from_column = Relationship._parse_table_column(from_combined)
        
        # Parsear toColumn (formato tabla.columna)
        to_combined = parser.get_property('toColumn')
        relationship.to_table, relationship.to_column = Relationship._parse_table_column(to_combined)
        
        relationship.cross_filtering_behavior = parser.get_property('crossFilteringBehavior')
        relationship.security_filtering_behavior = parser.get_property('securityFilteringBehavior')
        relationship.cardinality = parser.get_property('cardinality')
        relationship.is_active = parser.get_property('isActive', True)
    
    def save_to_file(self, filepath: Path):
        """Guarda la relación a un archivo .tmdl"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.raw_content)
