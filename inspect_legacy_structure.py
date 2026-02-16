"""Inspeccionar la estructura de sections en el reporte legacy."""

import json

report_path = r"D:\mcpdata\Toyota\TES - Systems Transformation\PanE CRM leadsOG.Report\report.json"

with open(report_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

sections = data.get('sections', [])
print(f'Total sections: {len(sections)}\n')

for i, section in enumerate(sections):
    print(f"Section {i}: {section.get('name', 'NO NAME')}")
    print(f"  Keys: {list(section.keys())}")
    
    # Mostrar visualContainers si existen
    visuals = section.get('visualContainers', [])
    print(f"  Visual containers: {len(visuals)}")
    
    for j, visual in enumerate(visuals[:3]):  # Primeros 3
        print(f"    Visual {j}: {visual.get('name', 'NO NAME')}")
    
    if len(visuals) > 3:
        print(f"    ... y {len(visuals) - 3} más")
    
    print()
