"""
Test para validar que el parseo de páginas legacy funciona correctamente.
Verifica que sections del formato antiguo se conviertan a Page objects.
"""

import json
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path para importar los módulos
sys.path.insert(0, str(Path(__file__).parent))

from models.report import clsReport

def test_legacy_pages_loading():
    """Prueba que las páginas del formato legacy se cargan correctamente desde sections."""
    
    # Ruta a la carpeta del reporte legacy en mcpdata
    report_path = r"D:\mcpdata\Toyota\TES - Systems Transformation\PanE CRM leadsOG.Report"
    
    if not os.path.exists(report_path):
        print(f"❌ ERROR: No se encontró la carpeta del reporte en {report_path}")
        return False
    
    try:
        print(f"✅ Carpeta del reporte encontrada: {report_path}")
        
        # Cargar el reporte
        report = clsReport(report_path)
        print(f"✅ Reporte cargado exitosamente")
        
        # Validar atributos detectados
        print(f"\n📊 Información del Reporte:")
        print(f"   - Formato detectado: {report.report_format}")
        print(f"   - SemanticModel: {report.SemanticModel}")
        print(f"   - semantic_model_id: {report.semantic_model_id}")
        
        # Validar páginas cargadas
        print(f"\n📄 Páginas Cargadas:")
        print(f"   - Total de páginas: {len(report.pages)}")
        print(f"   - Page Order: {report.pageOrder}")
        print(f"   - Primera página activa: {report.activePageName}")
        
        if len(report.pages) == 0:
            print(f"\n⚠️  ADVERTENCIA: No se cargaron páginas. Validando estructura...")
            
            # Validar que report_data tiene sections
            if report._report_data and 'sections' in report._report_data:
                sections = report._report_data['sections']
                print(f"   - Sections encontradas en JSON: {len(sections)}")
                for idx, section in enumerate(sections[:3]):  # Mostrar primeras 3
                    print(f"     * Section {idx}: {section.get('name', 'Sin nombre')}")
            else:
                print(f"   - No se encontró data en _report_data")
            
            return False
        
        # Validar primera página
        if report.pages:
            first_page = report.pages[0]
            print(f"\n📑 Primera Página:")
            print(f"   - Nombre: {getattr(first_page, 'name', 'N/A')}")
            print(f"   - Display Name: {getattr(first_page, 'displayName', 'N/A')}")
            print(f"   - Total visuals: {len(getattr(first_page, 'visuals', []))}")
            
            # Mostrar visuals
            if hasattr(first_page, 'visuals') and first_page.visuals:
                print(f"   - Visuals:")
                for visual in first_page.visuals[:3]:  # Primeros 3
                    print(f"     * {visual.name}")
        
        print(f"\n✅ TEST COMPLETADO EXITOSAMENTE")
        print(f"   El formato legacy se está parseando correctamente:")
        print(f"   - Páginas desde sections: {len(report.pages)}")
        print(f"   - Metadatos accesibles: ✓")
        return True
        
    except Exception as e:
        print(f"❌ Error al cargar el reporte: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_legacy_pages_loading()
    sys.exit(0 if success else 1)
