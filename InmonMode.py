from pathlib import Path
from models import SemanticModel, TableElementSpec, clsReport
from collections import defaultdict
import json

def scaffold_empty_report_and_pbip(model_name: str, models_path: Path) -> None:
    """Crea un .pbip y un .Report vacío enlazado al modelo."""
    import uuid
    
    base = model_name.replace('.SemanticModel', '')
    report_dir = models_path / f"{base}.Report"
    report_dir.mkdir(parents=True, exist_ok=True)

    # .platform (metadata del report)
    platform_path = report_dir / ".platform"
    platform_obj = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {
            "type": "Report",
            "displayName": base
        },
        "config": {
            "version": "2.0",
            "logicalId": str(uuid.uuid4())
        }
    }
    platform_path.write_text(json.dumps(platform_obj, indent=2), encoding="utf-8")

    # definition.pbir (link al modelo)
    pbir_path = report_dir / "definition.pbir"
    pbir_obj = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0",
        "datasetReference": {
            "byPath": {
                "path": f"../{model_name}"
            }
        }
    }
    pbir_path.write_text(json.dumps(pbir_obj, indent=2), encoding="utf-8")

    # Estructura básica de report
    definition_dir = report_dir / "definition"
    pages_dir = definition_dir / "pages"
    static_dir = report_dir / "StaticResources" / "SharedResources"
    definition_dir.mkdir(parents=True, exist_ok=True)
    pages_dir.mkdir(parents=True, exist_ok=True)
    static_dir.mkdir(parents=True, exist_ok=True)

    report_json = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.0.0/schema.json",
        "themeCollection": {
            "baseTheme": {
                "name": "CY25SU11",
                "reportVersionAtImport": {
                    "visual": "2.4.0",
                    "report": "3.0.0",
                    "page": "2.3.0"
                },
                "type": "SharedResources"
            }
        },
        "resourcePackages": [
            {
                "name": "SharedResources",
                "type": "SharedResources",
                "items": [
                    {
                        "name": "CY25SU11",
                        "path": "BaseThemes/CY25SU11.json",
                        "type": "BaseTheme"
                    }
                ]
            }
        ],
        "settings": {
            "useStylableVisualContainerHeader": True,
            "exportDataMode": "AllowSummarized",
            "defaultDrillFilterOtherVisuals": True,
            "allowChangeFilterTypes": True,
            "useEnhancedTooltips": True,
            "useDefaultAggregateDisplayName": True
        }
    }
    (definition_dir / "report.json").write_text(json.dumps(report_json, indent=2), encoding="utf-8")
    
    version_json = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
        "version": "2.0.0"
    }
    (definition_dir / "version.json").write_text(json.dumps(version_json, indent=2), encoding="utf-8")
    
    # Crear pages.json con una página vacía
    page_id = str(uuid.uuid4()).replace('-', '')[:20]  # ID de 20 caracteres
    pages_json = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": [page_id],
        "activePageName": page_id
    }
    (pages_dir / "pages.json").write_text(json.dumps(pages_json, indent=2), encoding="utf-8")
    
    # Crear directorio de página y archivo page.json
    page_folder = pages_dir / page_id
    page_folder.mkdir(parents=True, exist_ok=True)
    
    page_json = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json",
        "name": page_id,
        "displayName": "Página 1",
        "displayOption": "FitToPage",
        "height": 720,
        "width": 1280
    }
    (page_folder / "page.json").write_text(json.dumps(page_json, indent=2), encoding="utf-8")

    # Crear .pbip que apunte al report
    pbip_path = models_path / f"{base}.pbip"
    pbip_obj = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0",
        "artifacts": [
            {"report": {"path": f"{base}.Report"}}
        ],
        "settings": {"enableAutoRecovery": True}
    }
    pbip_path.write_text(json.dumps(pbip_obj, indent=2), encoding="utf-8")
    print(f"  ✅ Archivo .pbip creado: {pbip_path.name}")

def run_adventureworks_examples(semantic_model, base_path):
    """
    Ejecuta ejemplos de creación de submodelos específicos para FullAdventureWorks.
    Solo se ejecuta si el modelo cargado es FullAdventureWorks.
    """
    # ===== EJEMPLO 1: Submodelo simple con ManyToOne por defecto =====
    print("\n" + "="*60)
    print("EJEMPLO 1: SUBMODELO SIMPLE (SOLO MANYTOONE)")
    print("="*60)
    
    # Lista simple de tablas - usa ManyToOne por defecto
    initial_tables = [
        "FactInternetSales"
    ]
    
    try:
        subset_model_1 = semantic_model.create_subset_model(
            table_specs=initial_tables,
            subset_name="SimpleInternetSales.SemanticModel",
            recursive=True,
            max_depth=5
        )
        
        subset_output_1 = base_path / "Modelos" / "SimpleInternetSales.SemanticModel"
        print(f"\nGuardando submodelo en: {subset_output_1}")
        subset_model_1.save_to_directory(subset_output_1)
        
        # Crear .pbip y .Report vacío
        scaffold_empty_report_and_pbip("SimpleInternetSales.SemanticModel", base_path / "Modelos")
        
        print(f"\n¡Submodelo 1 creado!")
        print(f"  - Tablas incluidas: {len(subset_model_1.tables)}")
        print(f"  - Relaciones incluidas: {len(subset_model_1.relationships)}")
    except Exception as e:
        print(f"Error en Ejemplo 1: {e}")
    
    # ===== EJEMPLO 2: Submodelo con direcciones específicas =====
    print("\n" + "="*60)
    print("EJEMPLO 2: SUBMODELO CON DIRECCIONES ESPECÍFICAS")
    print("="*60)
    
    # Especificar dirección para cada tabla
    table_specs = [
        ("FactInternetSales", "ManyToOne"),      # Busca dimensiones relacionadas
        ("DimProduct", "Both"),                # Busca en ambas direcciones
        ("DimCustomer", "OneToMany")          # Busca tablas de hechos que usen esta dimensión
    ]
    
    try:
        subset_model_2 = semantic_model.create_subset_model(
            table_specs=table_specs,
            subset_name="AdvancedSales.SemanticModel",
            recursive=True,
            max_depth=3
        )
        
        subset_output_2 = base_path / "Modelos" / "AdvancedSales.SemanticModel"
        print(f"\nGuardando submodelo en: {subset_output_2}")
        subset_model_2.save_to_directory(subset_output_2)
        
        # Crear .pbip y .Report vacío
        scaffold_empty_report_and_pbip("AdvancedSales.SemanticModel", base_path / "Modelos")
        
        print(f"\n¡Submodelo 2 creado!")
        print(f"  - Tablas incluidas: {len(subset_model_2.tables)}")
        print(f"  - Relaciones incluidas: {len(subset_model_2.relationships)}")
        
        print(f"\nTablas en el submodelo avanzado:")
        for table in sorted(subset_model_2.tables, key=lambda t: t.name):
            print(f"  - {table.name}")
    except Exception as e:
        print(f"Error en Ejemplo 2: {e}")
    
    # ===== EJEMPLO 5: Submodelo con filtrado de elementos =====
    print("\n" + "="*60)
    print("EJEMPLO 5: SUBMODELO CON FILTRADO DE ELEMENTOS")
    print("="*60)
    
    try:
        # Definir qué elementos incluir/excluir por tabla
        element_specs = {
            "FactInternetSales": TableElementSpec(
                # Solo incluir estas columnas (las columnas de FK se agregarán automáticamente)
                columns=["SalesAmount", "OrderQuantity"],
                measures=["Total Sales"],
                mode='include'
            ),
            "DimProduct": TableElementSpec(
                # Solo incluir estos campos (ProductKey se agregará automáticamente si está en relaciones)
                columns=["EnglishProductName", "Color"],
                mode='include'
            ),
            "DimCustomer": TableElementSpec(
                # Excluir estas columnas EXCEPTO las que estén en relaciones
                columns=["Phone", "EmailAddress", "AddressLine1"],
                mode='exclude'
            )
        }
        
        subset_model_5 = semantic_model.create_subset_model(
            table_specs=[("FactInternetSales", "ManyToOne")],
            subset_name="FilteredSales.SemanticModel",
            recursive=True,
            max_depth=2,
            table_elements=element_specs
        )
        
        subset_output_5 = base_path / "Modelos" / "FilteredSales.SemanticModel"
        subset_model_5.save_to_directory(subset_output_5)
        
        # Crear .pbip y .Report vacío
        scaffold_empty_report_and_pbip("FilteredSales.SemanticModel", base_path / "Modelos")
        
        print(f"\n¡Submodelo 5 creado con elementos filtrados!")
        print(f"  - Tablas incluidas: {len(subset_model_5.tables)}")
        
        # Mostrar detalles de elementos filtrados
        print("\nDetalles de tablas filtradas:")
        for table in subset_model_5.tables:
            if table.name in element_specs:
                print(f"\n  Tabla '{table.name}':")
                print(f"    - Columnas: {len(table.columns)}")
                column_names = [col.name for col in table.columns]
                print(f"    - Nombres: {', '.join(column_names[:5])}{'...' if len(column_names) > 5 else ''}")
                print(f"    - Medidas: {len(table.measures)}")
    except Exception as e:
        print(f"Error en Ejemplo 5: {e}")
        import traceback
        traceback.print_exc()
    
    # ===== EJEMPLO 6: Submodelo basado en reportes =====
    print("\n" + "="*60)
    print("EJEMPLO 6: SUBMODELO BASADO EN REPORTES")
    print("="*60)
    
    try:
        # Buscar todos los directorios .Report en Modelos
        modelos_path = base_path / "Modelos"
        report_dirs = [d for d in modelos_path.iterdir() if d.is_dir() and d.name.endswith('.Report')]
        
        print(f"\nReportes encontrados: {len(report_dirs)}")
        
        # Diccionario para acumular todas las referencias de todos los reportes
        all_references = defaultdict(set)
        
        # Analizar cada reporte
        for report_dir in report_dirs:
            print(f"\n  Analizando: {report_dir.name}")
            report = clsReport(str(report_dir))
            
            # Obtener columnas usadas
            references = {table: sorted(list(cols)) for table, cols in report.get_all_columns_used().items()}
            
            print(f"    Referencias encontradas: {len(references)} tablas")
            
            # Acumular las referencias
            for table, columns in references.items():
                all_references[table].update(columns)
                print(f"    - {table}: {columns}")
        
        # Mostrar resumen consolidado
        print("\n" + "-"*60)
        print("RESUMEN CONSOLIDADO DE TODOS LOS REPORTES:")
        print("-"*60)
        total_columns = 0
        for table in sorted(all_references.keys()):
            columns = sorted(all_references[table])
            print(f"\n  {table}: {len(columns)} columnas")
            for col in columns:
                print(f"    - {col}")
            total_columns += len(columns)
        
        print(f"\n  Total: {len(all_references)} tablas, {total_columns} columnas/medidas")
        
        # Crear TableElementSpec para cada tabla
        # Todas las columnas/medidas encontradas en reportes se incluirán
        # Necesitamos distinguir entre columnas y medidas consultando el modelo original
        element_specs_from_reports = {}
        
        for table, fields in all_references.items():
            # Buscar la tabla en el modelo original
            original_table = next((t for t in semantic_model.tables if t.name == table), None)
            if not original_table:
                continue
            
            # Separar campos en columnas y medidas
            columns_list = []
            measures_list = []
            
            original_column_names = {col.name for col in original_table.columns}
            original_measure_names = {m.name for m in original_table.measures}
            
            for field in fields:
                if field in original_column_names:
                    columns_list.append(field)
                elif field in original_measure_names:
                    measures_list.append(field)
                else:
                    # Si no está en ninguno, asumir que es columna (podría ser alias)
                    columns_list.append(field)
            
            # Crear spec para incluir solo estas columnas/medidas
            # Las FK necesarias se agregarán automáticamente
            element_specs_from_reports[table] = TableElementSpec(
                columns=columns_list if columns_list else None,
                measures=measures_list if measures_list else None,
                mode='include'
            )
        
        # Extraer las tablas iniciales (todas las que aparecen en reportes)
        initial_tables = list(all_references.keys())
        
        print(f"\n\nCreando submodelo con {len(initial_tables)} tablas iniciales...")
        print("IMPORTANTE: Solo se incluirán estas tablas, sin tablas relacionadas adicionales")
        
        # Crear el submodelo
        # recursive=False para NO incluir tablas relacionadas
        subset_model_6 = semantic_model.create_subset_model(
            table_specs=initial_tables,  # Lista simple, usará ManyToOne por defecto
            subset_name="ReportBasedModel.SemanticModel",
            recursive=False,  # NO incluir tablas relacionadas automáticamente
            max_depth=0,  # No expandir
            table_elements=element_specs_from_reports
        )
        
        subset_output_6 = base_path / "Modelos" / "ReportBasedModel.SemanticModel"
        subset_model_6.save_to_directory(subset_output_6)
        
        # Crear .pbip y .Report vacío
        scaffold_empty_report_and_pbip("ReportBasedModel.SemanticModel", base_path / "Modelos")
        
        print(f"\n¡Submodelo basado en reportes creado!")
        print(f"  - Tablas incluidas: {len(subset_model_6.tables)}")
        print(f"  - Relaciones incluidas: {len(subset_model_6.relationships)}")
        
        print(f"\nTablas en el submodelo basado en reportes:")
        for table in sorted(subset_model_6.tables, key=lambda t: t.name):
            cols = [col.name for col in table.columns]
            measures = [m.name for m in table.measures]
            print(f"\n  {table.name}:")
            print(f"    - Columnas: {len(cols)}")
            if cols:
                print(f"      {', '.join(cols[:5])}{'...' if len(cols) > 5 else ''}")
            print(f"    - Medidas: {len(measures)}")
            if measures:
                print(f"      {', '.join(measures[:5])}{'...' if len(measures) > 5 else ''}")
                
    except Exception as e:
        print(f"Error en Ejemplo 6: {e}")
        import traceback
        traceback.print_exc()

def main():
    """
    Carga el modelo semántico FullAdventureWorks y crea una copia.
    También demuestra cómo crear un submodelo con tablas específicas.
    """
    # Definir rutas - usar la ruta del workspace actual
    base_path = Path(__file__).parent  # d:\Python apps\pyconstelaciones + Reports
    #base_path = Path("D:/Python apps/pyModeler")
    source_path = base_path / "Modelos" / "FullAdventureWorks.SemanticModel"
    target_path = base_path / "Modelos" / "FullAdventureWorksCopy.SemanticModel"
    
    # Instanciar el modelo semántico
    print(f"Cargando modelo desde: {source_path}")
    semantic_model = SemanticModel(str(source_path))
    
    # Cargar toda la estructura del directorio
    semantic_model.load_from_directory(source_path)
    
    print(f"Modelo cargado exitosamente:")
    print(f"  - Tablas: {len(semantic_model.tables)}")
    print(f"  - Relaciones: {len(semantic_model.relationships)}")
    print(f"  - Culturas: {len(semantic_model.cultures)}")
    print(f"  - Platform: {'Sí' if semantic_model.platform else 'No'}")
    print(f"  - Definition: {'Sí' if semantic_model.definition else 'No'}")
    print(f"  - Model: {'Sí' if semantic_model.model else 'No'}")
    
    # Mostrar particiones con colores
    print("\n" + "="*60)
    print("PARTICIONES DEL MODELO")
    print("="*60)
    
    # ANSI color codes
    GREEN = '\033[92m'  # Verde para import
    YELLOW = '\033[93m'  # Amarillo para directQuery
    CYAN = '\033[96m'   # Cian para dual
    RED = '\033[91m'    # Rojo para otros
    RESET = '\033[0m'   # Reset color
    
    total_partitions = 0
    import_count = 0
    directquery_count = 0
    dual_count = 0
    other_count = 0
    
    for table in sorted(semantic_model.tables, key=lambda t: t.name):
        if table.partitions:
            
            for partition in table.partitions:
                total_partitions += 1
                mode = partition.mode.lower() if partition.mode else 'unknown'
                
                if mode == 'import':
                    color = GREEN
                    import_count += 1
                elif mode == 'directquery':
                    color = YELLOW
                    print(f"  {color}• {table.name} [{mode}] - Tipo: {partition.source_type or 'N/A'}{RESET}")
                    directquery_count += 1
                elif mode == 'dual':
                    color = CYAN
                    dual_count += 1
                else:
                    color = RED
                    other_count += 1
                
                #print(f"  {color}• {partition.name} [{mode}] - Tipo: {partition.source_type or 'N/A'}{RESET}")
    
    # Resumen
    print("\n" + "-"*60)
    print("RESUMEN DE PARTICIONES:")
    print(f"  {GREEN}Import:{RESET} {import_count}")
    print(f"  {YELLOW}DirectQuery:{RESET} {directquery_count}")
    print(f"  {CYAN}Dual:{RESET} {dual_count}")
    print(f"  {RED}Otros:{RESET} {other_count}")
    print(f"  Total: {total_partitions}")
    print("-"*60)
    
    # Guardar la copia en el nuevo directorio
    print(f"\nGuardando copia en: {target_path}")
    #semantic_model.save_to_directory(target_path)
    
    print("\n¡Copia completada exitosamente!")
    
    # Ejecutar ejemplos solo si es FullAdventureWorks
    if "FullAdventureWorks" in str(source_path):
        print("\n" + "="*60)
        print("DETECTADO MODELO FULLADVENTUREWORKS - EJECUTANDO EJEMPLOS")
        print("="*60)
        run_adventureworks_examples(semantic_model, base_path)
    else:
        print(f"\nModelo '{source_path.name}' no es FullAdventureWorks - Omitiendo ejemplos")
    
if __name__ == "__main__":
    main()
