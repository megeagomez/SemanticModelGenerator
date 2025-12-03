from pathlib import Path
from typing import Optional, Dict, Any
from .tmdl_parser import TmdlParser

class Model:
    """
    Representa el archivo model.tmdl del modelo semántico.
    Formato TMDL (Tabular Model Definition Language).
    """
    
    def __init__(self):
        self.name: Optional[str] = None
        self.culture: Optional[str] = None
        self.data_access_options: Dict[str, Any] = {}
        self.default_power_bi_data_source_version: Optional[str] = None
        self.source_query_culture: Optional[str] = None
        self.annotations: Dict[str, Any] = {}
        self.raw_content: str = ""  # Contenido original
        
    @classmethod
    def from_file(cls, filepath: Path) -> 'Model':
        """Carga el modelo desde un archivo .tmdl"""
        instance = cls()
        with open(filepath, 'r', encoding='utf-8') as f:
            instance.raw_content = f.read()
        
        # Parsear contenido TMDL
        parser = TmdlParser(instance.raw_content)
        instance.name = parser.get_property('name')
        instance.culture = parser.get_property('culture')
        instance.data_access_options = parser.get_object('dataAccessOptions')
        instance.default_power_bi_data_source_version = parser.get_property('defaultPowerBIDataSourceVersion')
        instance.source_query_culture = parser.get_property('sourceQueryCulture')
        instance.annotations = parser.get_annotations()
        
        return instance
    
    def save_to_file(self, filepath: Path):
        """Guarda el modelo a un archivo .tmdl"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.raw_content)
    
    def mark_modified(self):
        """Marca este objeto como modificado"""
        # Este método será usado por SemanticModel para tracking
        pass
