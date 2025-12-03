"""
Script de debug para verificar qué está leyendo el ReportParser
"""

import json
from pathlib import Path
from models import ReportParser

def debug_report(report_path):
    """Debug detallado de un reporte"""
    print(f"\n{'='*80}")
    print(f"DEBUG: {report_path}")
    print('='*80)
    
    report_dir = Path(report_path)
    
    # 1. Verificar report.json
    report_json = report_dir / "definition" / "report.json"
    if report_json.exists():
        print(f"\n1. REPORT.JSON encontrado")
        with open(report_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'filterConfig' in data:
            print(f"   - Tiene filterConfig con {len(data['filterConfig'].get('filters', []))} filtros")
            for filt in data['filterConfig'].get('filters', []):
                if 'field' in filt:
                    print(f"     * {json.dumps(filt['field'], indent=8)}")
        else:
            print("   - NO tiene filterConfig")
    
    # 2. Verificar páginas
    pages_dir = report_dir / "definition" / "pages"
    if pages_dir.exists():
        page_dirs = [d for d in pages_dir.iterdir() if d.is_dir()]
        print(f"\n2. PÁGINAS: {len(page_dirs)} encontradas")
        
        for page_dir in page_dirs[:2]:  # Solo las primeras 2
            print(f"\n   Página: {page_dir.name}")
            
            page_json = page_dir / "page.json"
            if page_json.exists():
                with open(page_json, 'r', encoding='utf-8') as f:
                    page_data = json.load(f)
                
                if 'filterConfig' in page_data:
                    print(f"   - Page.json tiene {len(page_data['filterConfig'].get('filters', []))} filtros")
                    for filt in page_data['filterConfig'].get('filters', []):
                        if 'field' in filt:
                            print(f"     * {json.dumps(filt['field'], indent=8)}")
            
            # Visuales
            visuals_dir = page_dir / "visuals"
            if visuals_dir.exists():
                visual_dirs = [d for d in visuals_dir.iterdir() if d.is_dir()]
                print(f"   - Visuales: {len(visual_dirs)}")
                
                for visual_dir in visual_dirs[:2]:  # Solo los primeros 2
                    visual_json = visual_dir / "visual.json"
                    if visual_json.exists():
                        with open(visual_json, 'r', encoding='utf-8') as f:
                            visual_data = json.load(f)
                        
                        print(f"\n     Visual: {visual_dir.name}")
                        
                        # Query
                        if 'visual' in visual_data and 'query' in visual_data['visual']:
                            query = visual_data['visual']['query']
                            if 'queryState' in query:
                                print(f"       - Query tiene queryState")
                                for section, data in query['queryState'].items():
                                    if isinstance(data, dict) and 'projections' in data:
                                        print(f"         {section}: {len(data['projections'])} proyecciones")
                                        for proj in data['projections'][:2]:
                                            if 'field' in proj:
                                                print(f"           * {json.dumps(proj['field'], indent=12, ensure_ascii=False)[:200]}...")
                        
                        # Filtros
                        if 'filterConfig' in visual_data:
                            print(f"       - Visual.json tiene {len(visual_data['filterConfig'].get('filters', []))} filtros")
    
    # 3. Ejecutar el parser
    print(f"\n3. RESULTADO DEL PARSER:")
    parser = ReportParser(report_path)
    references = parser.parse()
    
    for table in sorted(references.keys()):
        print(f"   {table}: {sorted(references[table])}")

if __name__ == "__main__":
    debug_report(r"d:\Python apps\pyconstelaciones\Modelos\FullAdventureWorks.Report")
    debug_report(r"d:\Python apps\pyconstelaciones\Modelos\Second.Report")
