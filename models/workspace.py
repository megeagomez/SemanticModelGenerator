"""
Clase Workspace para representar y persistir workspaces de Power BI en DuckDB.
"""
from typing import Optional, Dict, Any


class Workspace:
    """Representa un workspace de Power BI con métodos para persistencia."""
    
    def __init__(
        self,
        id: str,
        displayName: str,
        description: str = "",
        type: str = "Workspace",
        capacityId: Optional[str] = None,
        domainId: Optional[str] = None
    ):
        """
        Inicia una instancia de Workspace.
        
        Args:
            id: ID único del workspace
            displayName: Nombre del workspace
            description: Descripción del workspace
            type: Tipo de workspace ('Workspace' o 'Personal')
            capacityId: ID de la capacidad (opcional)
            domainId: ID del dominio (opcional)
        """
        self.id = id
        self.displayName = displayName
        self.description = description
        self.type = type
        self.capacityId = capacityId
        self.domainId = domainId
    
    @classmethod
    def from_powerbi_response(cls, data: Dict[str, Any]) -> "Workspace":
        """
        Crea una instancia de Workspace desde la respuesta de la API de Power BI.
        
        Args:
            data: Diccionario con datos del workspace de la API
            
        Returns:
            Instancia de Workspace
        """
        return cls(
            id=data.get("id"),
            displayName=data.get("displayName", ""),
            description=data.get("description", ""),
            type=data.get("type", "Workspace"),
            capacityId=data.get("capacityId"),
            domainId=data.get("domainId")
        )
    
    def save_to_database(self, connection):
        """
        Guarda el workspace en la tabla 'workspaces' de DuckDB.
        
        Args:
            connection: Conexión DuckDB (duckdb.DuckDBPyConnection)
        """
        # Crear tabla si no existe
        connection.execute("""
            CREATE TABLE IF NOT EXISTS workspaces (
                id VARCHAR PRIMARY KEY,
                displayName VARCHAR NOT NULL,
                description VARCHAR,
                type VARCHAR,
                capacityId VARCHAR,
                domainId VARCHAR,
                created_at TIMESTAMP DEFAULT now(),
                updated_at TIMESTAMP DEFAULT now()
            )
        """)
        
        # Insertar o actualizar workspace (UPSERT)
        connection.execute("""
            INSERT INTO workspaces (id, displayName, description, type, capacityId, domainId, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, now())
            ON CONFLICT(id) DO UPDATE SET 
                displayName = excluded.displayName,
                description = excluded.description,
                type = excluded.type,
                capacityId = excluded.capacityId,
                domainId = excluded.domainId,
                updated_at = excluded.updated_at
        """, [
            self.id,
            self.displayName,
            self.description,
            self.type,
            self.capacityId,
            self.domainId
        ])
    
    def __repr__(self) -> str:
        return f"Workspace(id={self.id!r}, displayName={self.displayName!r}, type={self.type!r})"
