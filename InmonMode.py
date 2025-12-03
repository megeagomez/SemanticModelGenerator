from pathlib import Path
from models import SemanticModel, TableElementSpec, ReportParser
from collections import defaultdict

def main():
    """
    Carga el modelo semántico FullAdventureWorks y crea una copia.
    También demuestra cómo crear un submodelo con tablas específicas.
    """
    # Definir rutas - usar la ruta del workspace actual
    base_path = Path(__file__).parent  # d:\Python apps\pyconstelaciones + Reports
    source_path = base_path / "Modelos" / "FullAdventureWorks.SemanticModel"
    target_path = base_path / "Modelos" / "CopyofFullAdventureWorks.SemanticModel"
    
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
    
    # Guardar la copia en el nuevo directorio
    print(f"\nGuardando copia en: {target_path}")
    semantic_model.save_to_directory(target_path)
    
    print("\n¡Copia completada exitosamente!")
    
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
            parser = ReportParser(str(report_dir))
            references = parser.parse()
            
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
    
if __name__ == "__main__":
    main()
