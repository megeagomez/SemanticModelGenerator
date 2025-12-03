from pathlib import Path
import json
from typing import Optional

class Definition:
    """
    Representa el archivo definition.pbism (JSON) con la definición del modelo Power BI.
    """
    
    def __init__(self):
        self.version: Optional[str] = None
        self.metadata_version: Optional[str] = None
        self.raw_content: dict = {}
        
    @classmethod
    def from_file(cls, filepath: Path) -> 'Definition':
        """Carga desde archivo JSON"""
        instance = cls()
        
        with open(filepath, 'r', encoding='utf-8') as f:
            instance.raw_content = json.load(f)
        
        instance.version = instance.raw_content.get('version')
        instance.metadata_version = instance.raw_content.get('metadataVersion')
        
        return instance
    
    def save_to_file(self, filepath: Path):
        """Guarda a archivo JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.raw_content, f, indent=2, ensure_ascii=False)
