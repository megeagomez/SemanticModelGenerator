from typing import List, Optional, Set, Tuple, Literal, Dict
from pathlib import Path
import json
from enum import Enum

from .model import Model
from .relationship import Relationship
from .table import Table
from .culture import Culture
from .platform import Platform
from .definition import Definition

class RelationshipDirection(Enum):
    """Dirección de búsqueda de relaciones (NO la cardinalidad de la relación)"""
    MANY_TO_ONE = "ManyToOne"
    ONE_TO_MANY = "OneToMany"
    BOTH = "Both"

class TableElementSpec:
    """
    Especificación de elementos a incluir/excluir de una tabla.
    """
    def __init__(
        self,
        columns: Optional[List[str]] = None,
        measures: Optional[List[str]] = None,
        hierarchies: Optional[List[str]] = None,
        mode: Literal['include', 'exclude'] = 'include'
    ):
        self.columns = columns
        self.measures = measures
        self.hierarchies = hierarchies
        self.mode = mode
    
    def to_dict(self) -> dict:
        """Convierte a diccionario para serialización JSON"""
        return {
            'columns': self.columns,
            'measures': self.measures,
            'hierarchies': self.hierarchies,
            'mode': self.mode
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TableElementSpec':
        """Crea instancia desde diccionario"""
        return cls(
            columns=data.get('columns'),
            measures=data.get('measures'),
            hierarchies=data.get('hierarchies'),
            mode=data.get('mode', 'include')
        )

class SemanticModel:
    """
    Representa un modelo semántico completo de Power BI.
    Mantiene la estructura de carpetas y archivos originales.
    """
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.model: Optional[Model] = None
        self.relationships: List[Relationship] = []
        self.tables: List[Table] = []
        self.cultures: List[Culture] = []
        self.platform: Optional[Platform] = None
        self.definition: Optional[Definition] = None
        
        # Metadatos para reconstrucción
        self._file_metadata = {
            'model': {'original_path': None, 'modified': False},
            'relationships': {},
            'tables': {},
            'cultures': {},
            'platform': {'original_path': None, 'modified': False},
            'definition': {'original_path': None, 'modified': False}
        }
    
    def load_from_directory(self, directory: Path):
        """Carga toda la estructura desde un directorio."""
        self.base_path = directory
        
        # La mayoría de archivos están dentro de la carpeta definition
        definition_dir = directory / "definition"
        
        # Cargar model.tmdl (dentro de definition)
        model_path = definition_dir / "model.tmdl"
        if model_path.exists():
            self.model = Model.from_file(model_path)
            self._file_metadata['model']['original_path'] = str(model_path)
        
        # Cargar relationships.tmdl (archivo único dentro de definition)
        relationships_file = definition_dir / "relationships.tmdl"
        if relationships_file.exists():
            with open(relationships_file, 'r', encoding='utf-8') as f:
                relationships_content = f.read()
            
            # Parsear todas las relaciones del archivo
            self.relationships = Relationship.parse_all_from_content(relationships_content)
            self._file_metadata['relationships'] = {
                'original_path': str(relationships_file),
                'modified': False,
                'content': relationships_content
            }
        
        # Cargar tables (dentro de definition)
        tables_dir = definition_dir / "tables"
        if tables_dir.exists():
            for table_file in sorted(tables_dir.glob("*.tmdl")):
                table = Table.from_file(table_file)
                self.tables.append(table)
                self._file_metadata['tables'][table.name] = {
                    'original_path': str(table_file),
                    'modified': False
                }
        
        # Cargar cultures (dentro de definition)
        cultures_dir = definition_dir / "cultures"
        if cultures_dir.exists():
            for culture_file in sorted(cultures_dir.glob("*.tmdl")):
                culture = Culture.from_file(culture_file)
                self.cultures.append(culture)
                self._file_metadata['cultures'][culture.name] = {
                    'original_path': str(culture_file),
                    'modified': False
                }
        
        # Cargar definition.pbism (en la raíz)
        definition_path = directory / "definition.pbism"
        if definition_path.exists():
            self.definition = Definition.from_file(definition_path)
            self._file_metadata['definition']['original_path'] = str(definition_path)
        
        # Cargar .platform (en la raíz)
        platform_path = directory / ".platform"
        if platform_path.exists():
            self.platform = Platform.from_file(platform_path)
            self._file_metadata['platform']['original_path'] = str(platform_path)
    
    def save_to_directory(self, output_dir: Path, only_modified: bool = False):
        """Guarda la estructura a un directorio, manteniendo el orden original."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Crear carpeta definition
        definition_dir = output_dir / "definition"
        definition_dir.mkdir(exist_ok=True)
        
        # Guardar model.tmdl (dentro de definition)
        if self.model and (not only_modified or self._file_metadata['model']['modified']):
            self.model.save_to_file(definition_dir / "model.tmdl")
        
        # Guardar relationships.tmdl (archivo único dentro de definition)
        if self.relationships and (not only_modified or self._file_metadata['relationships']['modified']):
            relationships_file = definition_dir / "relationships.tmdl"
            with open(relationships_file, 'w', encoding='utf-8') as f:
                f.write(self._file_metadata['relationships']['content'])
        
        # Guardar tables (dentro de definition)
        if self.tables:
            tables_dir = definition_dir / "tables"
            tables_dir.mkdir(exist_ok=True)
            for table in self.tables:
                if not only_modified or self._file_metadata['tables'][table.name]['modified']:
                    table.save_to_file(tables_dir / f"{table.name}.tmdl")
        
        # Guardar cultures (dentro de definition)
        if self.cultures:
            cultures_dir = definition_dir / "cultures"
            cultures_dir.mkdir(exist_ok=True)
            for culture in self.cultures:
                if not only_modified or self._file_metadata['cultures'][culture.name]['modified']:
                    culture.save_to_file(cultures_dir / f"{culture.name}.tmdl")
        
        # Guardar definition.pbism (en la raíz)
        if self.definition and (not only_modified or self._file_metadata['definition']['modified']):
            self.definition.save_to_file(output_dir / "definition.pbism")
        
        # Guardar .platform (en la raíz)
        if self.platform and (not only_modified or self._file_metadata['platform']['modified']):
            self.platform.save_to_file(output_dir / ".platform")
    
    def create_subset_model(
        self, 
        table_specs: List[Tuple[str, str]] | List[str], 
        subset_name: str, 
        config_path: Optional[Path] = None,
        recursive: bool = True,
        max_depth: int = 10,
        table_elements: Optional[Dict[str, TableElementSpec]] = None
    ) -> 'SemanticModel':
        """
        Crea un subconjunto del modelo semántico con las tablas especificadas
        y todas las tablas relacionadas según el tipo de relación.
        
        Args:
            table_specs: Lista de tablas. Puede ser:
                - Lista de strings: nombres de tablas (usa ManyToOne por defecto)
                - Lista de tuplas (nombre, dirección_búsqueda): especifica dirección por tabla
                  dirección_búsqueda puede ser: "ManyToOne", "OneToMany", "Both"
                  NOTA: Esto es la DIRECCIÓN DE BÚSQUEDA, no la cardinalidad de las relaciones
            subset_name: Nombre del nuevo modelo semántico
            config_path: Ruta donde guardar el archivo de configuración (opcional)
            recursive: Si True, busca relaciones recursivamente
            max_depth: Profundidad máxima de recursión (previene ciclos infinitos)
            table_elements: Diccionario de especificaciones de elementos por tabla
        
        Returns:
            Nueva instancia de SemanticModel con el subconjunto
        
        Ejemplo:
            # Búsqueda simple con ManyToOne por defecto
            model.create_subset_model(["FactInternetSales", "DimProduct"], "SalesModel")
            
            # Búsqueda especificando direcciones
            model.create_subset_model([
                ("FactInternetSales", "ManyToOne"),
                ("DimProduct", "Both"),
                ("DimCustomer", "OneToMany")
            ], "SalesModel")
            
            # Con filtrado de elementos
            from models import TableElementSpec
            
            model.create_subset_model(
                table_specs=["Internet Sales"],
                subset_name="SalesModel",
                table_elements={
                    "Internet Sales": TableElementSpec(
                        columns=["SalesAmount", "OrderDate", "CustomerKey"],
                        measures=["Total Sales", "Average Sales"],
                        mode='include'
                    ),
                    "DimProduct": TableElementSpec(
                        columns=["InternalColumns"],
                        mode='exclude'
                    )
                }
            )
        """
        # Normalizar table_specs a lista de tuplas
        normalized_specs = []
        for spec in table_specs:
            if isinstance(spec, str):
                normalized_specs.append((spec, RelationshipDirection.MANY_TO_ONE.value))
            else:
                normalized_specs.append(spec)
        
        # Conjunto para almacenar todas las tablas a incluir
        tables_to_include: Set[str] = set()
        # CORREGIDO: Solo guardamos la dirección de búsqueda, no modificamos las relaciones
        table_search_configs: dict[str, str] = {}  # tabla -> dirección de búsqueda
        
        # Agregar tablas iniciales
        for table_name, search_direction in normalized_specs:
            tables_to_include.add(table_name)
            table_search_configs[table_name] = search_direction
        
        # Guardar el conjunto inicial de tablas (antes de expandir)
        # Esto se usará para filtrar relaciones cuando recursive=False
        initial_tables_only = tables_to_include.copy()
        
        # Buscar tablas relacionadas (recursivamente si se especifica)
        if recursive:
            self._find_related_tables_recursive(
                normalized_specs,
                tables_to_include,
                table_search_configs,
                current_depth=0,
                max_depth=max_depth
            )
        else:
            # Cuando recursive=False, NO expandir a tablas relacionadas
            # Solo incluir las tablas explícitamente especificadas
            pass
        
        # Determinar qué conjunto de tablas usar para relaciones
        # Si recursive=False, solo incluir relaciones entre tablas del conjunto inicial
        tables_for_relationships = initial_tables_only if not recursive else tables_to_include
        
        # Serializar table_elements para configuración
        table_elements_config = {}
        if table_elements:
            table_elements_config = {
                table_name: spec.to_dict()
                for table_name, spec in table_elements.items()
            }
        
        # Crear configuración
        config = {
            "name": subset_name,
            "base_model": self.base_path.name if self.base_path else "Unknown",
            "initial_tables": [
                {"name": name, "search_direction": direction} 
                for name, direction in normalized_specs
            ],
            "included_tables": sorted(list(tables_for_relationships)),
            "table_search_configs": table_search_configs,
            "table_elements": table_elements_config,
            "total_tables": len(tables_for_relationships),
            "recursive": recursive,
            "max_depth": max_depth,
            "creation_date": None
        }
        
        # Guardar configuración
        if config_path is None:
            config_path = self.base_path.parent / f"{subset_name}_config.json"
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"Configuración guardada en: {config_path}")
        print(f"Tablas iniciales: {len(normalized_specs)}")
        print(f"Tablas totales (incluyendo relacionadas): {len(tables_for_relationships)}")
        print(f"Búsqueda recursiva: {recursive}")
        
        # Mostrar configuración de tablas iniciales
        print(f"\nTablas iniciales con direcciones de búsqueda:")
        for name, direction in normalized_specs:
            print(f"  - {name}: búsqueda {direction}")
        
        # Crear nuevo modelo semántico
        subset_model = SemanticModel(str(self.base_path.parent / subset_name))
        
        # Copiar metadatos generales
        subset_model.model = self.model
        subset_model.platform = self.platform
        subset_model.definition = self.definition
        subset_model.cultures = self.cultures.copy()
        
        # CORREGIDO: Filtrar relaciones manteniendo sus propiedades originales
        # Solo incluimos relaciones donde AMBAS tablas están en el subconjunto
        # tables_for_relationships ya fue definido arriba
        
        subset_relationships = []
        for rel in self.relationships:
            if self._relationship_involves_tables(rel, tables_for_relationships):
                # Mantener la relación con TODAS sus propiedades originales
                # No modificamos cardinality, crossFilteringBehavior, etc.
                subset_relationships.append(rel)
        
        # Identificar columnas necesarias para las relaciones
        # Solo las relaciones que realmente se incluirán en el submodelo
        required_columns_by_table = self._get_required_columns_for_relationships(
            subset_relationships
        )
        
        # Filtrar y aplicar especificaciones de elementos a las tablas
        # Solo incluir tablas que están en tables_for_relationships
        subset_model.tables = []
        for table in self.tables:
            if table.name in tables_for_relationships:
                # Si hay especificación de elementos para esta tabla, aplicarla
                if table_elements and table.name in table_elements:
                    spec = table_elements[table.name]
                    
                    # Asegurar que las columnas de relaciones se incluyan
                    required_cols = required_columns_by_table.get(table.name, set())
                    adjusted_spec = self._adjust_spec_for_relationships(
                        spec, 
                        required_cols,
                        table.name
                    )
                    
                    filtered_table = table.filter_elements(
                        columns=adjusted_spec.columns,
                        measures=adjusted_spec.measures,
                        hierarchies=adjusted_spec.hierarchies,
                        mode=adjusted_spec.mode
                    )
                    subset_model.tables.append(filtered_table)
                    
                    # Marcar como modificado
                    if required_cols:
                        print(f"  Tabla '{table.name}' filtrada: {spec.mode} mode")
                        print(f"    Columnas de relaciones preservadas: {', '.join(required_cols)}")
                    else:
                        print(f"  Tabla '{table.name}' filtrada: {spec.mode} mode")
                else:
                    # Sin filtrado, incluir tabla completa
                    subset_model.tables.append(table)
        
        # Asignar relaciones filtradas (CON SUS PROPIEDADES ORIGINALES)
        subset_model.relationships = subset_relationships
        
        print(f"\nRelaciones preservadas con sus propiedades originales:")
        print(f"  Total: {len(subset_model.relationships)} relaciones")
        for rel in subset_model.relationships[:5]:  # Mostrar primeras 5 como ejemplo
            cardinality = rel.cardinality or "manyToOne (implícito)"
            active = "activa" if rel.is_active else "inactiva"
            print(f"  - {rel.from_table} -> {rel.to_table}: {cardinality}, {active}")
        if len(subset_model.relationships) > 5:
            print(f"  ... y {len(subset_model.relationships) - 5} más")
        
        # Actualizar metadatos
        subset_model._file_metadata = {
            'model': self._file_metadata['model'].copy(),
            'relationships': {
                'original_path': self._file_metadata['relationships'].get('original_path'),
                'modified': False,  # No modificamos las relaciones, solo filtramos
                'content': self._rebuild_relationships_content(subset_model.relationships)
            },
            'tables': {
                table.name: {
                    'original_path': self._file_metadata['tables'].get(table.name, {}).get('original_path'),
                    'modified': table_elements and table.name in table_elements
                }
                for table in subset_model.tables
            },
            'cultures': self._file_metadata['cultures'].copy(),
            'platform': self._file_metadata['platform'].copy(),
            'definition': self._file_metadata['definition'].copy()
        }
        
        return subset_model
    
    def _find_related_tables_recursive(
        self,
        initial_specs: List[Tuple[str, str]],
        tables_to_include: Set[str],
        table_search_configs: dict[str, str],
        current_depth: int,
        max_depth: int
    ):
        """
        Busca tablas relacionadas de forma recursiva.
        
        Args:
            initial_specs: Especificaciones iniciales de tablas con DIRECCIÓN DE BÚSQUEDA
            tables_to_include: Conjunto que se va llenando con tablas encontradas
            table_search_configs: Configuración de DIRECCIÓN DE BÚSQUEDA por tabla
            current_depth: Profundidad actual de recursión
            max_depth: Profundidad máxima permitida
        """
        if current_depth >= max_depth:
            print(f"Advertencia: Alcanzada profundidad máxima ({max_depth})")
            return
        
        # Tablas nuevas encontradas en esta iteración
        new_tables = []
        
        for table_name, search_direction in initial_specs:
            if table_name not in self._get_table_names():
                print(f"Advertencia: Tabla '{table_name}' no encontrada en el modelo")
                continue
            
            related = self._find_related_tables_by_direction(table_name, search_direction)
            
            for related_table in related:
                if related_table not in tables_to_include:
                    tables_to_include.add(related_table)
                    # Las tablas relacionadas heredan ManyToOne por defecto
                    if related_table not in table_search_configs:
                        table_search_configs[related_table] = RelationshipDirection.MANY_TO_ONE.value
                        new_tables.append((related_table, RelationshipDirection.MANY_TO_ONE.value))
        
        # Si encontramos nuevas tablas, continuar recursivamente
        if new_tables and current_depth + 1 < max_depth:
            self._find_related_tables_recursive(
                new_tables,
                tables_to_include,
                table_search_configs,
                current_depth + 1,
                max_depth
            )
    
    def _find_related_tables_by_direction(
        self, 
        table_name: str, 
        search_direction: str
    ) -> Set[str]:
        """
        Encuentra tablas relacionadas según la DIRECCIÓN DE BÚSQUEDA especificada.
        NO modifica la cardinalidad de las relaciones.
        
        Args:
            table_name: Nombre de la tabla
            search_direction: "ManyToOne", "OneToMany" o "Both" (dirección de búsqueda)
        
        Returns:
            Conjunto de nombres de tablas relacionadas
        """
        related_tables = set()
        
        for rel in self.relationships:
            # Asegurar que las propiedades están parseadas
            if not rel.from_table or not rel.to_table:
                from .tmdl_parser import TmdlParser
                parser = TmdlParser(rel.raw_content)
                from_combined = parser.get_property('fromColumn')
                to_combined = parser.get_property('toColumn')
                from .relationship import Relationship
                rel.from_table, rel.from_column = Relationship._parse_table_column(from_combined)
                rel.to_table, rel.to_column = Relationship._parse_table_column(to_combined)
            
            # IMPORTANTE: Determinar la cardinalidad REAL de la relación
            # (no la dirección de búsqueda del usuario)
            cardinality = rel.cardinality or "manyToOne"
            
            # ManyToOne BÚSQUEDA: desde la tabla Many (from) hacia la tabla One (to)
            if search_direction in [RelationshipDirection.MANY_TO_ONE.value, RelationshipDirection.BOTH.value]:
                if rel.from_table == table_name:
                    # Esta tabla está del lado Many, agregar el lado One
                    if "manyToOne" in cardinality.lower() or "many" in cardinality.lower():
                        related_tables.add(rel.to_table)
            
            # OneToMany BÚSQUEDA: desde la tabla One (to) hacia las tablas Many (from)
            if search_direction in [RelationshipDirection.ONE_TO_MANY.value, RelationshipDirection.BOTH.value]:
                if rel.to_table == table_name:
                    # Esta tabla está del lado One, agregar el lado Many
                    if "manyToOne" in cardinality.lower() or "many" in cardinality.lower():
                        related_tables.add(rel.from_table)
        
        return related_tables
    
    @classmethod
    def load_from_config(cls, config_path: Path, base_models_dir: Path) -> 'SemanticModel':
        """
        Carga un modelo semántico basado en un archivo de configuración.
        
        Args:
            config_path: Ruta al archivo de configuración JSON
            base_models_dir: Directorio donde se encuentran los modelos base
        
        Returns:
            Nueva instancia de SemanticModel según la configuración
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Cargar el modelo base
        base_model_path = base_models_dir / config['base_model']
        base_model = cls(str(base_model_path))
        base_model.load_from_directory(base_model_path)
        
        # Reconstruir table_specs desde la configuración
        if 'initial_tables' in config and isinstance(config['initial_tables'], list):
            if len(config['initial_tables']) > 0 and isinstance(config['initial_tables'][0], dict):
                # Formato nuevo: [{"name": "...", "search_direction": "..."}]
                # También soportar formato antiguo con "direction"
                table_specs = [
                    (
                        table_info['name'], 
                        table_info.get('search_direction', table_info.get('direction', 'ManyToOne'))
                    )
                    for table_info in config['initial_tables']
                ]
            else:
                # Formato antiguo: lista de strings
                table_specs = config['initial_tables']
        else:
            # Fallback: usar included_tables con ManyToOne por defecto
            table_specs = config.get('included_tables', [])
        
        # Reconstruir table_elements si existe
        table_elements = None
        if 'table_elements' in config and config['table_elements']:
            table_elements = {
                table_name: TableElementSpec.from_dict(spec_dict)
                for table_name, spec_dict in config['table_elements'].items()
            }
        
        # Recrear el subconjunto
        subset_model = base_model.create_subset_model(
            table_specs=table_specs,
            subset_name=config['name'],
            config_path=config_path,
            recursive=config.get('recursive', True),
            max_depth=config.get('max_depth', 10),
            table_elements=table_elements
        )
        
        return subset_model
    
    def _get_required_columns_for_relationships(
        self, 
        relationships: List[Relationship]
    ) -> Dict[str, Set[str]]:
        """
        Identifica qué columnas son necesarias para las relaciones.
        
        Args:
            relationships: Lista de relaciones del submodelo
        
        Returns:
            Diccionario {tabla: {columna1, columna2, ...}}
        """
        required_columns = {}
        
        for rel in relationships:
            # Asegurar que las propiedades están parseadas
            if not rel.from_table or not rel.to_table:
                from .tmdl_parser import TmdlParser
                parser = TmdlParser(rel.raw_content)
                from_combined = parser.get_property('fromColumn')
                to_combined = parser.get_property('toColumn')
                from .relationship import Relationship
                rel.from_table, rel.from_column = Relationship._parse_table_column(from_combined)
                rel.to_table, rel.to_column = Relationship._parse_table_column(to_combined)
            
            # Agregar columna origen
            if rel.from_table and rel.from_column:
                if rel.from_table not in required_columns:
                    required_columns[rel.from_table] = set()
                required_columns[rel.from_table].add(rel.from_column)
            
            # Agregar columna destino
            if rel.to_table and rel.to_column:
                if rel.to_table not in required_columns:
                    required_columns[rel.to_table] = set()
                required_columns[rel.to_table].add(rel.to_column)
        
        return required_columns
    
    def _adjust_spec_for_relationships(
        self,
        original_spec: TableElementSpec,
        required_columns: Set[str],
        table_name: str
    ) -> TableElementSpec:
        """
        Ajusta la especificación de elementos para incluir columnas de relaciones.
        
        Args:
            original_spec: Especificación original del usuario
            required_columns: Columnas requeridas por relaciones
            table_name: Nombre de la tabla (para logging)
        
        Returns:
            Nueva especificación ajustada
        """
        if not required_columns:
            return original_spec
        
        adjusted_columns = original_spec.columns
        
        if original_spec.mode == 'include':
            # Modo include: agregar columnas de relaciones si no están
            if adjusted_columns is None:
                # Si no se especificaron columnas, None significa "todas"
                # No necesitamos ajustar
                pass
            else:
                # Asegurar que las columnas de relaciones están incluidas
                columns_set = set(adjusted_columns)
                missing_cols = required_columns - columns_set
                
                if missing_cols:
                    adjusted_columns = list(columns_set | required_columns)
                    print(f"    [!] Agregando columnas de relaciones a '{table_name}': {', '.join(missing_cols)}")
        
        elif original_spec.mode == 'exclude':
            # Modo exclude: asegurar que no se excluyan columnas de relaciones
            if adjusted_columns is not None:
                columns_set = set(adjusted_columns)
                conflicting_cols = required_columns & columns_set
                
                if conflicting_cols:
                    # Remover columnas de relaciones de la lista de exclusión
                    adjusted_columns = list(columns_set - required_columns)
                    print(f"    [!] Preservando columnas de relaciones en '{table_name}': {', '.join(conflicting_cols)}")
        
        # Crear nueva especificación con columnas ajustadas
        return TableElementSpec(
            columns=adjusted_columns,
            measures=original_spec.measures,
            hierarchies=original_spec.hierarchies,
            mode=original_spec.mode
        )
    
    def _get_table_names(self) -> Set[str]:
        """Obtiene el conjunto de nombres de todas las tablas del modelo."""
        return {table.name for table in self.tables}
    
    def _relationship_involves_tables(self, relationship: Relationship, table_names: Set[str]) -> bool:
        """
        Verifica si una relación involucra solo tablas del conjunto especificado.
        
        Args:
            relationship: Relación a verificar
            table_names: Conjunto de nombres de tablas permitidas
        
        Returns:
            True si ambas tablas de la relación están en el conjunto
        """
        if not relationship.from_table or not relationship.to_table:
            from .tmdl_parser import TmdlParser
            parser = TmdlParser(relationship.raw_content)
            from_combined = parser.get_property('fromColumn')
            to_combined = parser.get_property('toColumn')
            from .relationship import Relationship
            relationship.from_table, relationship.from_column = Relationship._parse_table_column(from_combined)
            relationship.to_table, relationship.to_column = Relationship._parse_table_column(to_combined)
        
        return (relationship.from_table in table_names and 
                relationship.to_table in table_names)
    
    def _rebuild_relationships_content(self, relationships: List[Relationship]) -> str:
        """
        Reconstruye el contenido del archivo relationships.tmdl con las relaciones filtradas.
        
        Args:
            relationships: Lista de relaciones a incluir
        
        Returns:
            Contenido completo del archivo relationships.tmdl
        """
        if not relationships:
            return ""
        
        content_parts = []
        for rel in relationships:
            content_parts.append(rel.raw_content)
        
        return '\n\n'.join(content_parts)
    
    def _find_directly_related_tables(self, table_name: str) -> Set[str]:
        """
        Encuentra todas las tablas directamente relacionadas con la tabla especificada.
        [DEPRECATED] Usar _find_related_tables_by_direction en su lugar.
        
        Args:
            table_name: Nombre de la tabla a analizar
        
        Returns:
            Conjunto de nombres de tablas relacionadas
        """
        related_tables = set()
        
        for rel in self.relationships:
            # Parsear las propiedades de la relación si no están cargadas
            if not rel.from_table or not rel.to_table:
                from .tmdl_parser import TmdlParser
                parser = TmdlParser(rel.raw_content)
                from_combined = parser.get_property('fromColumn')
                to_combined = parser.get_property('toColumn')
                from .relationship import Relationship
                rel.from_table, rel.from_column = Relationship._parse_table_column(from_combined)
                rel.to_table, rel.to_column = Relationship._parse_table_column(to_combined)
            
            # Verificar si la tabla está involucrada en la relación
            if rel.from_table == table_name:
                related_tables.add(rel.to_table)
            elif rel.to_table == table_name:
                related_tables.add(rel.from_table)
        
        return related_tables
