from pathlib import Path
import json
from typing import Optional

class Platform:
    """
    Representa el archivo .platform (JSON) que contiene metadatos de la plataforma.
    """
    
    def __init__(self):
        self.version: Optional[str] = None
        self.settings: dict = {}
        self.raw_content: dict = {}
        
    @classmethod
    def from_file(cls, filepath: Path) -> 'Platform':
        """Carga desde archivo JSON"""
        instance = cls()
        
        with open(filepath, 'r', encoding='utf-8') as f:
            instance.raw_content = json.load(f)
        
        instance.version = instance.raw_content.get('version')
        instance.settings = instance.raw_content.get('settings', {})
        
        return instance
    
    def save_to_file(self, filepath: Path):
        """Guarda a archivo JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.raw_content, f, indent=2, ensure_ascii=False)
