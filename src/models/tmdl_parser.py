import re
from typing import Any, Dict, Optional

class TmdlParser:
    """
    Parser para el formato TMDL (Tabular Model Definition Language).
    Formato personalizado similar a YAML pero con sus propias reglas.
    """
    
    def __init__(self, content: str):
        self.content = content
        self.lines = content.split('\n')
        
    def get_property(self, property_name: str, default: Any = None) -> Any:
        """Obtiene el valor de una propiedad simple"""
        pattern = rf'^\s*{property_name}\s*[:=]\s*(.+)$'
        
        for line in self.lines:
            match = re.match(pattern, line.strip())
            if match:
                value = match.group(1).strip()
                # Eliminar comillas si las tiene
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # Convertir booleanos
                if value.lower() == 'true':
                    return True
                elif value.lower() == 'false':
                    return False
                
                return value
        
        return default
    
    def get_object(self, object_name: str) -> Dict[str, Any]:
        """Obtiene un objeto completo como diccionario"""
        result = {}
        in_object = False
        indent_level = 0
        
        for line in self.lines:
            if object_name in line and ('{' in line or ':' in line):
                in_object = True
                indent_level = len(line) - len(line.lstrip())
                continue
            
            if in_object:
                current_indent = len(line) - len(line.lstrip())
                
                if current_indent <= indent_level and line.strip():
                    break
                
                # Parsear propiedades del objeto
                match = re.match(r'^\s*(\w+)\s*[:=]\s*(.+)$', line)
                if match:
                    key = match.group(1)
                    value = match.group(2).strip()
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    result[key] = value
        
        return result
    
    def get_annotations(self) -> Dict[str, Any]:
        """Obtiene todas las anotaciones"""
        annotations = {}
        in_annotations = False
        
        for line in self.lines:
            if 'annotation' in line.lower():
                in_annotations = True
                continue
            
            if in_annotations:
                match = re.match(r'^\s*(\w+)\s*=\s*(.+)$', line)
                if match:
                    key = match.group(1)
                    value = match.group(2).strip()
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    annotations[key] = value
                elif line.strip() and not line.strip().startswith('//'):
                    in_annotations = False
        
        return annotations
    
    def get_expression(self) -> str:
        """Obtiene una expresión DAX (usualmente multilinea)"""
        expression_lines = []
        in_expression = False
        
        for line in self.lines:
            if 'expression' in line.lower() and '=' in line:
                in_expression = True
                # Capturar la primera línea si tiene contenido
                parts = line.split('=', 1)
                if len(parts) > 1:
                    first_line = parts[1].strip()
                    if first_line:
                        expression_lines.append(first_line)
                continue
            
            if in_expression:
                if line.strip() and not line.strip().startswith('//'):
                    if re.match(r'^\s*\w+\s*[:=]', line):
                        break
                    expression_lines.append(line)
        
        return '\n'.join(expression_lines)
