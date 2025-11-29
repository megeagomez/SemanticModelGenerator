"""
Script de prueba para ReportParser
"""

from models import ReportParser
import json

def test_report_parser():
    """Prueba el parser con los reportes disponibles"""
    
    # Listar los reportes disponibles con rutas absolutas
    reports = [
        r"d:\Python apps\pyconstelaciones\Modelos\FullAdventureWorks.Report",
        r"d:\Python apps\pyconstelaciones\Modelos\Second.Report"
    ]
    
    for report_path in reports:
        print(f"\n{'='*80}")
        print(f"Analizando: {report_path}")
        print('='*80)
        
        try:
            parser = ReportParser(report_path)
            references = parser.parse()
            
            # Mostrar resumen
            print(parser.get_summary())
            
            # Mostrar diccionario detallado
            print("\n\nDiccionario de referencias (JSON):")
            print(json.dumps(references, indent=2, ensure_ascii=False))
            
        except Exception as e:
            print(f"Error al procesar {report_path}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_report_parser()
