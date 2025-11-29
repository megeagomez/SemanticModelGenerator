# Historia de Prompts - Desarrollo de la Biblioteca de Modelos Semánticos

Este documento contiene todos los prompts utilizados durante el desarrollo de esta biblioteca de clases para manipular modelos semánticos de Power BI.

---

## 1. Prompt Inicial - Creación de la Estructura Base

**Prompt:**
> Quiero hacer una biblioteca de clases que se corresponda con la estructura de la carpeta que hay bajo Modelos/FullAdventureWorks.SemanticModel. Con una clase modelo que incluya, model, relationship. un array de tables, y de cultures, un objeto .platform y un objeto definition.pbism, algunos de ellos son json y otros un formato personalizado que parece pero no es YAML, por favor mira dentro de los archivos e infiere las propiedades que han de tener los objetos. Por favor, recuerda que luego tendremos que hacer una carpeta igual, con la misma estructura en el mismo orden aunque ligeramente manipulada, así que por favor anota también el archivo original por si queda inalterado

**Resultado:**
- Creación de las clases base: `SemanticModel`, `Model`, `Relationship`, `Table`, `Culture`, `Platform`, `Definition`
- Implementación de `TmdlParser` para parsear el formato TMDL personalizado
- Sistema de metadatos para tracking de archivos modificados
- Métodos `load_from_directory` y `save_to_directory`

---

## 2. Prompt - Crear Script de Ejecución

**Prompt:**
> creame el codigo en el fichero InnmonMode.py que instancie la clase semantic_model, lea FullAdventureWorks.SemanticModel y lo copie a CopyofFullAdventureWorks.SemanticModel

**Resultado:**
- Creación del archivo `InmonMode.py`
- Script básico para cargar y copiar modelos completos

---

## 3. Prompt - Corrección de Estructura de Carpetas

**Prompt:**
> en la linea 57 el directorio tables, el directorio cultures y los archivos database.tmdl, model.tmdl y relationships.tmdl están dentro de la carpeta definition, por lo que no carga ni tablas ni definiciones

**Resultado:**
- Corrección de rutas para buscar archivos dentro de `definition/`
- Actualización de `load_from_directory` y `save_to_directory`

---

## 4. Prompt - Corrección de Estructura de Tablas

**Prompt:**
> dentro del directorio tables las tablas se encuentran en ficheros de extension .tmdl no son directorios por lo que table_dir.is_dir de la linea 63 no es adecuado y de la misma forma el metodo "from_directory" de Table no es adecuado, habría de ser from file y leer ese archivo de extensión tmdl

**Resultado:**
- Cambio de `Table.from_directory()` a `Table.from_file()`
- Las tablas se cargan desde archivos `.tmdl` individuales
- Parsing de columnas, medidas y particiones embebidas en el archivo

---

## 5. Prompt - Corrección de Archivo de Relaciones

**Prompt:**
> en la linea 50 relationships no es un directorio, sino un fichero que cuelga de definition y se llama relationships.tmdl, comprueba que lo escribí bien y arregla para que carge y copie las relaciones

**Resultado:**
- Cambio de directorio `relationships/` a archivo `relationships.tmdl`
- Implementación de `Relationship.parse_all_from_content()`
- Múltiples relaciones en un solo archivo

---

## 6. Prompt - Corrección de Formato de Relaciones

**Prompt:**
> en los archivos relationship.tmdl no están separados los atributos fromtable totable, sino que en fromcolumn, tocolumn incluye ambas, nombre de la tabla y nombre de la columna, si la tabla es una palabra reservada o tiene espacios la guarda así 'Internet Sales'.'Due Date Key', aunque en dax no se comportaria de esta manera. solamente lo hace en el fichero relationships.tmdl

**Resultado:**
- Implementación de `_parse_table_column()` para parsear formato `tabla.columna`
- Soporte para nombres con espacios: `'Internet Sales'.'Due Date Key'`
- Extracción correcta de tabla y columna de las relaciones

---

## 7. Prompt - Creación de Submodelos con Relaciones

**Prompt:**
> Quiero añadir un método a la clase semantic_model, el método recibirá una lista con nombres de tabla, buscará esas tablas en la relaciones y añadirá la lista de tablas con relaciones directas, para cada una de las tablas incluidas en el modelo. Esta petieición además de la lista de tablas llevará como parámetro un nombre, Ese nombre será el nombre del nuevo modelo semántico que va a incluir exclusivamente las tablas que relacionemos. El nombre suministrado junto con las tablas que lo acompañan se guardará en un archivo de configuracion con extensión .json que permitirá repetir el proceso y en un futuro le añadiremos algunas propiedades adicionales. me gustaría que me generaras ese método y que me dieras un ejemplo de llamada en el fichero InnmonMode.py

**Resultado:**
- Método `create_subset_model()` para crear subconjuntos del modelo
- Búsqueda automática de tablas relacionadas
- Generación de archivo de configuración JSON
- Método `load_from_config()` para recargar desde configuración

---

## 8. Prompt - Direcciones de Relación y Búsqueda Recursiva

**Prompt:**
> para cada tabla que incluyamos en el modelo reducido necesitamos decir de que lado de la relación buscamos más tablas, de manera predeterminada solo será del Many to One, es decir, FactInternetSales tiene relaciones Many to One con DimCustomer, DimCurrency, etc, DimProduct Tiene relacion Many To One con DimProductCategory, pero relacion one to many por ejemplo con FactReseller sales, por lo tanto las tablas no pueden ser unicamente su nombre sino que al menos tienen que ser una tupla nombre,tipode relacion, de manera predeterminada será manyToOne, el único camino a incluir, pero si por lo que sea se nos pone el OneToMany también lo buscaría. Además en la búsqueda, podemos poner un parámetro "recursive" de manera que si le decimos la tabla FactInternetSales, Many to One, y como general esta búsqueda es recursive, buscará todas las many to One para las tablas que aparezcan en Related_tables

**Resultado:**
- Enum `RelationshipDirection` con valores `ManyToOne`, `OneToMany`, `Both`
- Parámetro `table_specs` como lista de tuplas `(nombre, dirección)`
- Parámetro `recursive` para búsqueda recursiva
- Parámetro `max_depth` para controlar profundidad
- Métodos `_find_related_tables_by_direction()` y `_find_related_tables_recursive()`

---

## 9. Prompt - Generar Documentación

**Prompt:**
> Generame un directorio que se llame Documentation, dentro del directorio generame tantos archivos markdown como clases, en el primero de ellos me incluyes un esquema de clases con sus propiedesde y links a cada uno de los subfichero que explican las clases, además pon ejemplo de uso, tanto si la leemos de un archivo como si modificamos sus propiedades.

**Resultado:**
- Carpeta `Documentation/` con archivos Markdown
- `README.md` principal con esquema de clases
- Documentación individual para cada clase
- Ejemplos de uso completos
- Casos de uso reales

---

## 10. Prompt - Actualización de Documentación

**Prompt:**
> ¿me actualizas también la documentacion?

**Resultado:**
- Actualización de `SemanticModel.md` con nuevos parámetros
- Documentación de direcciones de relación
- Ejemplos de búsqueda recursiva
- Actualización de `README.md` con casos de uso

---

## 11. Prompt - Corrección de Configuración Initial Tables

**Prompt:**
> creo que initial_Tables en la linea 45 necesita una revision para que se incluya el tipo de relacion

**Resultado:**
- Corrección del formato de `initial_tables` en el JSON
- Uso de `normalized_specs` con tuplas correctas
- Preservación de direcciones en la configuración

---

## 12. Prompt - Corrección de Método Faltante

**Prompt:**
> [Error: AttributeError: 'SemanticModel' object has no attribute '_relationship_involves_tables']

**Resultado:**
- Implementación de `_relationship_involves_tables()`
- Implementación de `_rebuild_relationships_content()`
- Corrección de errores de ejecución

---

## 13. Prompt - Corrección de load_from_config

**Prompt:**
> [Error: TypeError: SemanticModel.create_subset_model() got an unexpected keyword argument 'table_names']

**Resultado:**
- Corrección de `load_from_config()` para usar `table_specs`
- Reconstrucción correcta de tuplas desde JSON
- Soporte para formatos antiguos y nuevos de configuración

---

## 14. Prompt - Añadir Filtrado de Elementos de Tabla

**Prompt:**
> Me gustaría añadir la posibilidad de que se eligieran de cada tabla un conjunto de columnas, jerarquias y métricas de dos manereas distintas, bien diciendo que las que paso se incluyan o bien diciendo que se quiten y que al generar el modelo derivado, se aplicara esa lógica a cada tabla

**Resultado:**
- Clase `TableElementSpec` para especificar filtros
- Métodos `filter_elements()` en la clase `Table`
- Modos `include` y `exclude` para filtrado
- Parámetro `table_elements` en `create_subset_model()`
- Serialización en configuración JSON

---

## 15. Prompt - Preservación de Columnas de Relaciones

**Prompt:**
> aunque se excluyan columnas las que participan de las relaciones entre tablas que existan en el nuevo modelo no se pueden quitar ¿me corriges esa parte?

**Resultado:**
- Método `_get_required_columns_for_relationships()`
- Método `_adjust_spec_for_relationships()`
- Preservación automática de columnas FK
- Advertencias cuando se agregan/preservan columnas
- Garantía de integridad referencial

---

## 16. Prompt - Corrección de Variable No Inicializada

**Prompt:**
> [Error: UnboundLocalError: cannot access local variable 'required_columns_by_table' where it is not associated with a value]

**Resultado:**
- Reordenamiento de código en `create_subset_model()`
- Filtrado de relaciones antes de filtrado de tablas
- Inicialización correcta de variables

---

## 17. Prompt - Corrección de Manejo de Excepciones

**Prompt:**
> por favor repasa inmonMode.py para que funcione adecuadamente con la llamada ahora me dice [error de tabla no encontrada]

**Resultado:**
- Añadido de bloques try-except en `InmonMode.py`
- Mejor manejo de errores
- Continuación de ejecución aunque fallen ejemplos
- Corrección de nombres de tablas

---

## 18. Prompt - Preservación de Atributos de Columnas

**Prompt:**
> en algunas tablas con la ejecucion del modelo filtrado hemos perdido muchísimos atributos en las tablas, entre otros las particiones que son obligatorias. Me gustaría que se preservara todo, excepto las columnas que se elimian, pero las que se quedan se quedan con todos sus atributos

**Resultado:**
- Reescritura completa del método `_filter_raw_content()`
- Parser línea por línea del contenido TMDL original
- Preservación de TODOS los atributos de columnas
- Preservación OBLIGATORIA de particiones
- Mantenimiento de formato y comentarios originales
- Deprecación de `_rebuild_raw_content()`

---

## 19. Prompt - Crear Documento de Historia de Prompts

**Prompt:**
> Me puedes crear un fichero .md con todos los prompts que he usado para que creemos esta app ?

**Resultado:**
- Este documento (`PROMPTS_HISTORY.md`)

---

## 20. Prompt - Separar Dirección de Búsqueda de Cardinalidad de Relaciones

**Prompt:**
> Ahora he detectado un pequeño bug. Cuando utilizamos el table_specs y le decimos "manyToOne" o OneToMany o Both , en realidad esta usando eso luego como la dirección de la relacion, y son dos cosas distintas. Lo que buscamos obtener con este parámetro es la direccion en la que buscamos tablas relacionadas para traernos, pero se ha de respetar la direccion original de las relaciones sin modificarla, asi que son dos cosas distintas. Por favor repasa el metódo create_subset_model para que tenga esto en consideracion

**Resultado:**
- Aclaración de conceptos: **Dirección de búsqueda** vs **Cardinalidad de relación**
- Renombrado de variables: `table_configs` → `table_search_configs`
- JSON usa `search_direction` en lugar de `direction`
- Las relaciones se copian con **TODAS** sus propiedades originales intactas
- No se modifica `cardinality`, `crossFilteringBehavior`, `isActive`, etc.
- Documentación actualizada explicando la diferencia
- Mensajes informativos mostrando preservación de propiedades

---

## 21. Prompt - Corrección de Métodos Auxiliares Faltantes

**Prompt:**
> [Error: AttributeError: 'SemanticModel' object has no attribute '_get_table_names']

**Resultado:**
- Implementación de `_get_table_names()`
- Implementación de `_relationship_involves_tables()`
- Implementación de `_rebuild_relationships_content()`
- Implementación de `_find_directly_related_tables()` (marcado como deprecated)

---

## 22. Prompt - Parser de Reportes (.Report) y extracción de referencias

**Prompt:**
> ¿me generas una clase llamada parsea Report, que se recorra estas carpetas y que para el report, devuelva un diccionario con esquema Tabla,Columna, que contenga los pares tabla-columna, tabla-medida, etc que usa?

**Resultado:**
- Creación de `models/report_parser.py` con la clase `ReportParser`
- Soporta extracción de referencias en:
    - `definition/report.json` (filtros a nivel de informe)
    - `definition/pages/*/page.json` (filtros a nivel de página)
    - `definition/pages/*/visuals/*/visual.json` (queries y filtros por visual)
- Soporte para campos de tipo `Column`, `Aggregation(Column)`, y `Measure`
- Función de conveniencia `parse_report(path)`
- Corrección de tipos de retorno para permitir `Optional[str]` en helpers

---

## 23. Prompt - Integración: crear submodelo con columnas usadas en reportes

**Prompt:**
> ahora añademe una llamda a las referencias de todos los .report que hay en mi directorio /Modelos y une las referencias, para pasarselo como element_Specs a create_subset_model y crear un submodelo con exclusivamente las columnas y métricas usadas en los reportes

**Resultado:**
- Actualización de `InmonMode.py` para:
    - Detectar todos los directorios `.Report` bajo `Modelos`
    - Parsear y consolidar referencias `tabla → columnas`
    - Construir `TableElementSpec` con `mode='include'` por tabla
    - Llamar a `create_subset_model(..., table_elements=element_specs_from_reports)`
- Añadido resumen consolidado por consola

---

## 24. Prompt - Corrección de rutas del workspace

**Prompt:**
> el error por el que no estas encontrando es que las rutas apuntan a d:\python app\pyconstelaciones , pero yo hice una copia en d:\python app\pyconstelaciones + Reports

**Resultado:**
- `InmonMode.py` ahora usa `base_path = Path(__file__).parent` para trabajar en el workspace actual (`pyconstelaciones + Reports`)
- Verificación y ejecución con el intérprete de la venv local

---

## 25. Prompt - Eliminar caracteres Unicode problemáticos en consola

**Prompt:**
> Error 'charmap' codec can't encode character '⚠' / '→'

**Resultado:**
- Reemplazo de `⚠` por `[!]` y `→` por `->` en `models/semantic_model.py`
- El output por consola ya no falla por codificación

---

## 26. Prompt - Submodelo estrictamente con tablas/columnas de reportes

**Prompt:**
> yo quiero que tenga exclusivamente las que se usan en el report, ni las relacionadas arriba o abajo ni ninguna que no sea necesaria.

**Resultado:**
- `InmonMode.py`: `create_subset_model(..., recursive=False, max_depth=0)`
- `SemanticModel.create_subset_model` actualizado para:
    - Mantener relaciones solo entre tablas del conjunto inicial cuando `recursive=False`
    - Incluir exclusivamente columnas especificadas y mínimas FKs requeridas por dichas relaciones
    - Configuración JSON refleja solo las tablas finales (`included_tables`)
- Resultado: submodelo con 8 tablas (las de los reportes) y columnas exactas + FKs mínimas

---

## 27. Prompts de verificación de contenido y depuración

**Prompts clave:**
- Ver el contenido de `visual.json` y `page.json` de ambos reportes (PowerShell `Get-Content | ConvertFrom-Json`)
- Scripts de debug (`debug_report.py`) para inspeccionar `queryState`, `filterConfig` y referencias detectadas
- Ejecución de pruebas (`test_report_parser.py`) con rutas absolutas y venv

**Trabajo realizado:**
- Creación de `debug_report.py` y `test_report_parser.py`
- Comprobación de que `Second.Report` inicialmente reflejaba contenido idéntico al de `FullAdventureWorks.Report`
- Ajuste de rutas y validación de referencias reales:
    - `FullAdventureWorks.Report` usa: `CurrencyName`, `SpanishProductCategoryName`, `MaritalStatus`, `OrderQuantity`, `SalesAmount`, `CalendarYear`
    - `Second.Report` usa: `SpanishProductCategoryName`, `SpanishProductSubcategoryName`, `SpanishProductName`, `Color`, `SalesAmount (FactResellerSales)`

---

## Resumen adicional del trabajo reciente

- Nueva clase: `ReportParser` + función `parse_report`
- Integración en `models/__init__.py` para exportar `ReportParser`
- Ejemplo 6 en `InmonMode.py`: creación de `ReportBasedModel.SemanticModel`
- Corrección de codificación por consola
- Estricta inclusión de tablas/columnas según reportes con FKs mínimas
- Confirmación por consola: 8 tablas, 10 columnas/medidas únicas consolidadas


## Resumen de Funcionalidades Implementadas

### Estructura Base
1. ✅ Clases para todos los componentes del modelo semántico
2. ✅ Parser TMDL personalizado
3. ✅ Sistema de tracking de modificaciones
4. ✅ Carga y guardado de modelos completos

### Creación de Submodelos
5. ✅ Método `create_subset_model()` con múltiples opciones
6. ✅ **Direcciones de búsqueda**: ManyToOne, OneToMany, Both
7. ✅ **Preservación de relaciones**: Cardinalidad y propiedades originales intactas
8. ✅ Búsqueda recursiva con control de profundidad
9. ✅ Configuración JSON persistente con `search_direction`

### Filtrado de Elementos
10. ✅ Filtrado de columnas, medidas y jerarquías
11. ✅ Modos include/exclude
12. ✅ Preservación automática de columnas de relaciones
13. ✅ Preservación de todos los atributos originales
14. ✅ Preservación obligatoria de particiones

### Documentación
15. ✅ Documentación completa en Markdown
16. ✅ Ejemplos de uso para cada funcionalidad
17. ✅ Casos de uso reales
18. ✅ Aclaración de conceptos (búsqueda vs cardinalidad)
19. ✅ Esta historia de prompts actualizada

---

## Conceptos Clave Aclarados

### Dirección de Búsqueda (Search Direction)
- **Qué es**: Parámetro del usuario para determinar qué tablas incluir
- **Valores**: `"ManyToOne"`, `"OneToMany"`, `"Both"`
- **Efecto**: Solo determina qué tablas relacionadas se agregan al submodelo
- **NO afecta**: Las propiedades de las relaciones

### Cardinalidad de Relación (Relationship Cardinality)
- **Qué es**: Propiedad de cada relación en el modelo
- **Valores**: `"manyToOne"`, `"oneToMany"`, `"oneToOne"`, etc.
- **Ubicación**: En `relationship.cardinality` del archivo TMDL
- **Preservación**: Siempre se mantiene intacta al crear submodelos

### Ejemplo Clarificador
```python
# Usuario especifica dirección de BÚSQUEDA
model.create_subset_model(
    table_specs=[("FactInternetSales", "ManyToOne")],
    subset_name="SalesModel"
)

# Sistema busca tablas siguiendo dirección ManyToOne:
# FactInternetSales → DimProduct (incluir)
# FactInternetSales → DimCustomer (incluir)

# Pero las relaciones se copian CON SUS PROPIEDADES ORIGINALES:
# Relación 1: cardinality="manyToOne", isActive=true, crossFilteringBehavior="oneDirection"
# Relación 2: cardinality="manyToOne", isActive=false, crossFilteringBehavior="bothDirections"
```

