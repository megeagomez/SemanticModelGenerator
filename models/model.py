from pathlib import Path
from typing import Optional, Dict, Any
from .tmdl_parser import TmdlParser
import json

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

    def save_to_database(self, connection):
        """
        Guarda el modelo semántico en DuckDB.
        
        Args:
            connection: Conexión DuckDB (duckdb.DuckDBPyConnection)
        """
        # Crear secuencias si no existen
        connection.execute("""
            CREATE SEQUENCE IF NOT EXISTS seq_semantic_model_id START 1
        """)
        
        # Crear tabla semantic_model
        connection.execute("""
            CREATE TABLE IF NOT EXISTS semantic_model (
                id INTEGER PRIMARY KEY DEFAULT nextval('seq_semantic_model_id'),
                name VARCHAR UNIQUE NOT NULL,
                culture VARCHAR,
                default_power_bi_data_source_version VARCHAR,
                source_query_culture VARCHAR,
                data_access_options JSON,
                annotations JSON,
                created_at TIMESTAMP DEFAULT now(),
                updated_at TIMESTAMP DEFAULT now()
            )
        """)
        
        # Insertar modelo
        connection.execute("""
            INSERT INTO semantic_model (name, culture, default_power_bi_data_source_version, source_query_culture, data_access_options, annotations)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET updated_at = now()
        """, [
            self.name,
            self.culture,
            self.default_power_bi_data_source_version,
            self.source_query_culture,
            json.dumps(self.data_access_options) if self.data_access_options else None,
            json.dumps(self.annotations) if self.annotations else None
        ])
