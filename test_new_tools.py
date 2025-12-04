#!/usr/bin/env python3
"""
Script de prueba para las nuevas herramientas del servidor MCP
"""

import asyncio
from pathlib import Path
from mcp_server import PowerBIModelServer

async def test_tools():
    """Prueba las nuevas herramientas del servidor MCP"""
    
    # Crear servidor con ruta de modelos
    models_path = Path(__file__).parent / "Modelos"
    server = PowerBIModelServer(models_path)
    
    # Probar get_report_pages
    print("=" * 80)
    print("Probando get_report_pages...")
    print("=" * 80)
    result = await server._get_report_pages("FullAdventureWorks.Report")
    print(result[0].text)
    
    # Probar get_page_visuals (necesitamos el nombre de una página primero)
    print("\n" + "=" * 80)
    print("Probando get_page_visuals...")
    print("=" * 80)
    
    # Primero obtenemos las páginas
    pages_result = await server._get_report_pages("FullAdventureWorks.Report")
    # Extraer el nombre de la primera página (está en formato "1. **nombre**")
    pages_text = pages_result[0].text
    # Buscar la primera línea que contiene un número seguido de punto
    for line in pages_text.split('\n'):
        if line.strip().startswith('1.'):
            # Extraer nombre entre "- Nombre: " y salto de línea
            if '- Nombre:' in pages_text:
                page_name = pages_text.split('- Nombre:')[1].split('\n')[0].strip()
                print(f"Usando página: {page_name}")
                visuals_result = await server._get_page_visuals("FullAdventureWorks.Report", page_name)
                print(visuals_result[0].text[:1000])  # Primeros 1000 caracteres
                break
    
    # Probar generate_report_svg
    print("\n" + "=" * 80)
    print("Probando generate_report_svg...")
    print("=" * 80)
    svg_result = await server._generate_report_svg("FullAdventureWorks.Report", page_name=None, save_to_file=False)
    svg_text = svg_result[0].text
    print(f"SVG generado: {len(svg_text)} caracteres")
    print("Primeros 500 caracteres:")
    print(svg_text[:500])
    
    # Guardar SVG a archivo
    print("\n" + "=" * 80)
    print("Guardando SVG a archivo...")
    print("=" * 80)
    svg_result_file = await server._generate_report_svg("FullAdventureWorks.Report", page_name=None, save_to_file=True)
    print(svg_result_file[0].text)

if __name__ == "__main__":
    asyncio.run(test_tools())
