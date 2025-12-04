"""Test parsing multi-line measures with triple backticks"""
from models.table import Table

# Sample TMDL content with multi-line measure using ```
sample_tmdl = """table pedidos
	lineageTag: abc123

	measure 'Pedidos netos' = ```
		
		/* Miguel Egea, 15-10-2025 se quitan las anulaciones cuando no se toman 
		esta era la formula original  [PedidosRealizados]-[Anulaciones de pedidos]+0 */
		var _pedidos = CALCULATE([# Pedidos], Dim_Estados_Pedido[BK_id_estado_Pedido] in {3,4,6,7})
		Return _pedidos
		```
	formatString: #,0
	lineageTag: 2f34cd97-7001-4a70-ac47-878dda65ebdb

	annotation DaxDependencies = Para la medida DAX proporcionada...

	measure 'Otra medida' = SUM(tabla[campo])
		formatString: 0.00

	partition pedidos = m
		mode: import
		source =
			let
				Source = ...
			in
				Source
"""

# Parse measures
measures = Table._parse_measures(sample_tmdl)

print(f"Found {len(measures)} measures:\n")
for m in measures:
	print(f"Measure: '{m.name}'")
	print(f"Format: {m.format_string}")
	print(f"Expression preview: {m.expression[:100] if len(m.expression) > 100 else m.expression}")
	print(f"Full expression length: {len(m.expression)} chars")
	print(f"Full expression:\n{m.expression}\n")
	print("-" * 80)
