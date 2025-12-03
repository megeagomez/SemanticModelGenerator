from pathlib import Path
from typing import Optional
from .tmdl_parser import TmdlParser

class Culture:
    """
    Representa una cultura/idioma del modelo.
    """
    
    def __init__(self):
        self.name: str = ""
        self.linguistic_metadata: Optional[str] = None
        self.raw_content: str = ""
        
    @classmethod
    def from_file(cls, filepath: Path) -> 'Culture':
        """Carga la cultura desde un archivo .tmdl"""
        instance = cls()
        instance.name = filepath.stem
        
        with open(filepath, 'r', encoding='utf-8') as f:
            instance.raw_content = f.read()
        
        parser = TmdlParser(instance.raw_content)
        instance.linguistic_metadata = parser.get_property('linguisticMetadata')
        
        return instance
    
    def save_to_file(self, filepath: Path):
        """Guarda la cultura a un archivo .tmdl"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.raw_content)
