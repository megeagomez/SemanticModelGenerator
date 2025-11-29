# TmdlParser

Utilidad para parsear el formato TMDL (Tabular Model Definition Language).

## Descripción

TMDL es un formato personalizado similar a YAML pero con sus propias reglas específicas para modelos tabulares de Power BI.

## Métodos

### `__init__(content: str)`

Inicializa el parser con el contenido TMDL.

### `get_property(property_name: str, default: Any = None) -> Any`

Obtiene el valor de una propiedad simple.

### `get_object(object_name: str) -> Dict[str, Any]`

Obtiene un objeto completo como diccionario.

### `get_annotations() -> Dict[str, Any]`

Obtiene todas las anotaciones.

### `get_expression() -> str`

Obtiene una expresión DAX (usualmente multilínea).

## Ejemplos de Uso

```python
from models.tmdl_parser import TmdlParser

content = """
table Sales
    lineageTag: abc123
    isHidden: false
    
    annotation PBI_Id = "Sales_123"
    annotation __PBI_TimeIntelligenceEnabled = 1
    
    column Amount
        dataType: decimal
        formatString: #,##0.00
"""

parser = TmdlParser(content)

# Obtener propiedades simples
tag = parser.get_property('lineageTag')
is_hidden = parser.get_property('isHidden')

# Obtener anotaciones
annotations = parser.get_annotations()
print(annotations)  # {'PBI_Id': 'Sales_123', '__PBI_TimeIntelligenceEnabled': '1'}
```

## Formato TMDL

### Propiedades Simples

```tmdl
propertyName: value
anotherProperty: "quoted value"
booleanProperty: true
```

### Objetos

```tmdl
objectName
    property1: value1
    property2: value2
```

### Expresiones DAX

```tmdl
measure TotalSales =
    SUM(Sales[Amount])
    formatString: #,##0.00
```

## Ver También

- [Model](Model.md) - Usa TmdlParser
- [Table](Table.md) - Usa TmdlParser
- [Relationship](Relationship.md) - Usa TmdlParser
