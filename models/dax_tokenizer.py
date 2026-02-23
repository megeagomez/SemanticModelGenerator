"""
DaxTokenizer – Tokenizador y analizador de dependencias DAX.

Tokeniza expresiones DAX y extrae dependencias:
  - Tablas referenciadas (Tabla[Columna])
  - Columnas usadas
  - Medidas referenciadas ([Medida])
  - Funciones DAX invocadas
  - Variables definidas (VAR)

Incluye resolución transitiva de medidas (A→B→C) con detección
de ciclos para evitar recursión infinita.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, FrozenSet, List, Optional, Set, Tuple


# ──────────────────────────────────────────────
# Token types
# ──────────────────────────────────────────────

class TokenType(Enum):
    FUNCTION = auto()
    TABLE_REF = auto()       # Tabla (parte izquierda de Tabla[Col])
    COLUMN_REF = auto()      # [Col] cuando viene con tabla
    MEASURE_REF = auto()     # [Medida] sola, sin tabla
    VARIABLE = auto()        # VAR nombre = ...
    KEYWORD = auto()         # RETURN, EVALUATE, ORDER BY, etc.
    OPERATOR = auto()        # +, -, *, /, =, <>, etc.
    NUMBER = auto()
    STRING = auto()          # "texto"
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    WHITESPACE = auto()
    NEWLINE = auto()
    COMMENT = auto()
    UNKNOWN = auto()


@dataclass
class Token:
    type: TokenType
    value: str
    pos: int = 0


@dataclass
class DaxDependencies:
    """Resultado de analizar una expresión DAX."""
    tables: Set[str] = field(default_factory=set)
    columns: Dict[str, Set[str]] = field(default_factory=dict)   # tabla → {cols}
    measures: Set[str] = field(default_factory=set)
    functions: Set[str] = field(default_factory=set)
    variables: Set[str] = field(default_factory=set)

    def add_column(self, table: str, column: str):
        self.tables.add(table)
        self.columns.setdefault(table, set()).add(column)


# ──────────────────────────────────────────────
# DAX function catalogue  (~350 funciones de dax.guide)
# ──────────────────────────────────────────────

DAX_FUNCTIONS: FrozenSet[str] = frozenset({
    # Aggregate
    "APPROXIMATEDISTINCTCOUNT", "AVERAGE", "AVERAGEA", "AVERAGEX",
    "COUNT", "COUNTA", "COUNTAX", "COUNTBLANK", "COUNTROWS", "COUNTX",
    "DISTINCTCOUNT", "DISTINCTCOUNTNOBLANK",
    "MAX", "MAXA", "MAXX", "MIN", "MINA", "MINX",
    "PRODUCT", "PRODUCTX",
    "SUM", "SUMX",
    # Date & Time
    "CALENDAR", "CALENDARAUTO",
    "DATE", "DATEDIFF", "DATEVALUE", "DAY",
    "EDATE", "EOMONTH",
    "HOUR", "MINUTE", "MONTH", "NOW", "QUARTER", "SECOND",
    "TIME", "TIMEVALUE", "TODAY",
    "UTCNOW", "UTCTODAY",
    "WEEKDAY", "WEEKNUM", "YEAR", "YEARFRAC",
    # Filter
    "ALL", "ALLCROSSFILTERED", "ALLEXCEPT", "ALLNOBLANKROW", "ALLSELECTED",
    "CALCULATE", "CALCULATETABLE",
    "EARLIER", "EARLIEST",
    "FILTER",
    "HASONEFILTER", "HASONEVALUE",
    "ISBLANK", "ISCROSSFILTERED", "ISEMPTY", "ISFILTERED",
    "KEEPFILTERS",
    "LOOKUPVALUE",
    "REMOVEFILTERS",
    "SELECTEDVALUE",
    "USERELATIONSHIP",
    "VALUES",
    # Financial
    "ACCRINT", "ACCRINTM", "AMORDEGRC", "AMORLINC",
    "COUPDAYBS", "COUPDAYS", "COUPDAYSNC", "COUPNCD", "COUPNUM", "COUPPCD",
    "CUMIPMT", "CUMPRINC",
    "DB", "DDB", "DISC", "DOLLARDE", "DOLLARFR", "DURATION",
    "EFFECT", "FV",
    "INTRATE", "IPMT", "ISPMT",
    "MDURATION",
    "NOMINAL", "NPER",
    "ODDFPRICE", "ODDFYIELD", "ODDLPRICE", "ODDLYIELD",
    "PDURATION", "PMT", "PPMT",
    "PRICE", "PRICEDISC", "PRICEMAT", "PV",
    "RATE", "RECEIVED", "RRI",
    "SLN", "SYD",
    "TBILLEQ", "TBILLPRICE", "TBILLYIELD",
    "VDB",
    "XIRR", "XNPV",
    "YIELD", "YIELDDISC", "YIELDMAT",
    # Information
    "COLUMNSTATISTICS",
    "CONTAINS", "CONTAINSROW", "CONTAINSSTRING", "CONTAINSSTRINGEXACT",
    "CUSTOMDATA",
    "HASONEFILTER", "HASONEVALUE",
    "ISAFTER", "ISBLANK", "ISCROSSFILTERED", "ISEMPTY", "ISERROR",
    "ISEVEN", "ISFILTERED", "ISINSCOPE", "ISLOGICAL", "ISNONTEXT",
    "ISNUMBER", "ISODD", "ISONORAFTER", "ISSELECTEDMEASURE", "ISSUBTOTAL",
    "ISTEXT",
    "NONVISUAL",
    "SELECTEDMEASURE", "SELECTEDMEASUREFORMATSTRING", "SELECTEDMEASURENAME",
    "USERCULTURE", "USERNAME", "USEROBJECTID", "USERPRINCIPALNAME",
    # Logical
    "AND", "BITAND", "BITOR", "BITXOR", "BITLSHIFT", "BITRSHIFT",
    "COALESCE",
    "FALSE", "IF", "IF.EAGER", "IFERROR",
    "NOT", "OR",
    "SWITCH", "TRUE",
    # Math & Trig
    "ABS", "ACOS", "ACOSH", "ACOT", "ACOTH",
    "ASIN", "ASINH", "ATAN", "ATANH",
    "CEILING", "COMBIN", "COMBINA",
    "CONVERT", "COS", "COSH", "COT", "COTH",
    "CURRENCY",
    "DEGREES", "DIVIDE",
    "EVEN", "EXP", "FACT",
    "FLOOR", "GCD",
    "INT", "ISO.CEILING",
    "LCM", "LN", "LOG", "LOG10",
    "MOD", "MROUND",
    "ODD",
    "PERMUT",
    "PI", "POWER",
    "QUOTIENT",
    "RADIANS", "RAND", "RANDBETWEEN", "ROUND", "ROUNDDOWN", "ROUNDUP",
    "SIGN", "SIN", "SINH", "SQRT", "SQRTPI",
    "TAN", "TANH", "TRUNC",
    # Other
    "BLANK", "ERROR",
    "EXCEPT", "INTERSECT",
    "GENERATESERIES",
    "GROUPBY",
    "NATURALINNERJOIN", "NATURALLEFTOUTERJOIN",
    "SUMMARIZECOLUMNS",
    "TREATAS",
    "UNION",
    # Parent & Child
    "PATH", "PATHCONTAINS", "PATHITEM", "PATHITEMREVERSE", "PATHLENGTH",
    # Relationship
    "CROSSFILTER", "RELATED", "RELATEDTABLE", "USERELATIONSHIP",
    # Statistical
    "BETA.DIST", "BETA.INV",
    "CHISQ.DIST", "CHISQ.DIST.RT", "CHISQ.INV", "CHISQ.INV.RT",
    "CONFIDENCE.NORM", "CONFIDENCE.T",
    "EXPON.DIST",
    "GEOMEAN", "GEOMEANX",
    "MEDIAN", "MEDIANX",
    "NORM.DIST", "NORM.INV", "NORM.S.DIST", "NORM.S.INV",
    "PERCENTILE.EXC", "PERCENTILE.INC",
    "PERCENTILEX.EXC", "PERCENTILEX.INC",
    "POISSON.DIST",
    "RANKX",
    "SAMPLE", "STDEV.P", "STDEV.S", "STDEVX.P", "STDEVX.S",
    "T.DIST", "T.DIST.2T", "T.DIST.RT", "T.INV", "T.INV.2T",
    "VAR.P", "VAR.S", "VARX.P", "VARX.S",
    # Table manipulation
    "ADDCOLUMNS", "ADDMISSINGITEMS",
    "CROSSJOIN",
    "CURRENTGROUP",
    "DATATABLE",
    "DETAILROWS",
    "DISTINCT",
    "GENERATE", "GENERATEALL", "GENERATESERIES",
    "GROUPBY",
    "IGNORE",
    "NATURALINNERJOIN", "NATURALLEFTOUTERJOIN",
    "ROLLUP", "ROLLUPADDISSUBTOTAL", "ROLLUPISSUBTOTAL", "ROLLUPGROUP",
    "ROW",
    "SELECTCOLUMNS",
    "SUBSTITUTEWITHINDEX",
    "SUMMARIZE", "SUMMARIZECOLUMNS",
    "TOPN",
    "TREATAS",
    "UNION",
    "VALUES",
    # Text
    "COMBINEVALUES", "CONCATENATE", "CONCATENATEX",
    "EXACT",
    "FIND",
    "FIXED", "FORMAT",
    "LEFT", "LEN", "LOWER",
    "MID",
    "REPLACE", "REPT", "RIGHT",
    "SEARCH", "SUBSTITUTE",
    "TRIM",
    "UNICHAR", "UNICODE", "UPPER", "VALUE",
    # Time Intelligence
    "CLOSINGBALANCEMONTH", "CLOSINGBALANCEQUARTER", "CLOSINGBALANCEYEAR",
    "DATEADD", "DATESBETWEEN", "DATESINPERIOD",
    "DATESMINPERIOD", "DATESMTD", "DATESQTD", "DATESYTD",
    "ENDOFMONTH", "ENDOFQUARTER", "ENDOFYEAR",
    "FIRSTDATE", "FIRSTNONBLANK", "FIRSTNONBLANKVALUE",
    "LASTDATE", "LASTNONBLANK", "LASTNONBLANKVALUE",
    "NEXTDAY", "NEXTMONTH", "NEXTQUARTER", "NEXTYEAR",
    "OPENINGBALANCEMONTH", "OPENINGBALANCEQUARTER", "OPENINGBALANCEYEAR",
    "PARALLELPERIOD",
    "PREVIOUSDAY", "PREVIOUSMONTH", "PREVIOUSQUARTER", "PREVIOUSYEAR",
    "SAMEPERIODLASTYEAR",
    "STARTOFMONTH", "STARTOFQUARTER", "STARTOFYEAR",
    "TOTALMTD", "TOTALQTD", "TOTALYTD",
    # Window / ORDERBY / OFFSET (new DAX)
    "INDEX", "OFFSET", "WINDOW",
    "ORDERBY", "PARTITIONBY",
    "MATCHBY",
    "RANK",
    # Row context
    "ADDCOLUMNS", "SELECTCOLUMNS",
    "DEFINE", "EVALUATE", "MEASURE",
})

DAX_KEYWORDS: FrozenSet[str] = frozenset({
    "VAR", "RETURN", "EVALUATE", "ORDER", "BY", "ASC", "DESC",
    "DEFINE", "MEASURE", "COLUMN", "TABLE",
    "TRUE", "FALSE", "BLANK",
    "IN", "NOT", "AND", "OR",
})


# ──────────────────────────────────────────────
# Regex patterns for first pass
# ──────────────────────────────────────────────

# Quoted table name with column: 'Tabla con espacios'[Columna]
_RE_QUOTED_TABLE_COL = re.compile(
    r"'([^']+)'\s*\[([^\]]+)\]"
)

# Unquoted table name with column: Tabla[Columna]
_RE_UNQUOTED_TABLE_COL = re.compile(
    r"(?<!')(\b[A-Za-z_]\w*(?:\s+\w+)*?)\s*\[([^\]]+)\]"
)

# Standalone measure reference: [Medida]  (not preceded by table name or ')
_RE_MEASURE_REF = re.compile(
    r"(?<!['\w\]\s])\[([^\]]+)\]"
)

# String literal
_RE_STRING = re.compile(r'"(?:[^"]*"")*[^"]*"')

# Line / block comments
_RE_LINE_COMMENT = re.compile(r'//[^\n]*')
_RE_BLOCK_COMMENT = re.compile(r'/\*.*?\*/', re.DOTALL)

# Number: integer or decimal
_RE_NUMBER = re.compile(r'\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b')

# Identifier/word
_RE_WORD = re.compile(r'\b[A-Za-z_][\w.]*\b')

# Operators
_RE_OPERATOR = re.compile(r'<>|>=|<=|&&|\|\||[+\-*/=<>&|^]')


# ──────────────────────────────────────────────
# DaxTokenizer class
# ──────────────────────────────────────────────

class DaxTokenizer:
    """
    Tokeniza expresiones DAX y extrae dependencias.

    Uso básico::

        tk = DaxTokenizer(known_tables, known_measures)
        deps = tk.analyze(expression)

    Carga desde DuckDB::

        tk = DaxTokenizer.from_duckdb(path, model_id)
        all_deps = tk.analyze_all_measures(measures_dict)
        trans = tk.resolve_transitive_measures(all_deps)
    """

    def __init__(
        self,
        known_tables: Optional[Set[str]] = None,
        known_measures: Optional[Dict[str, str]] = None,
        known_columns: Optional[Dict[str, Set[str]]] = None,
    ):
        """
        Args:
            known_tables:   Conjunto de nombres de tablas del modelo.
            known_measures: Diccionario {nombre_medida: expression} de todas
                            las medidas del modelo.
            known_columns:  Diccionario {tabla: {col1, col2, ...}}.
        """
        self.known_tables: Set[str] = known_tables or set()
        self.known_measures: Dict[str, str] = known_measures or {}
        self.known_columns: Dict[str, Set[str]] = known_columns or {}
        # Mapa lower → original para lookup insensible a mayúsculas
        self._measures_lower: Dict[str, str] = {
            k.lower(): k for k in self.known_measures
        }
        self._tables_lower: Dict[str, str] = {
            t.lower(): t for t in self.known_tables
        }

    # ──────────────────────────────────────────
    # Public: analyze single expression
    # ──────────────────────────────────────────

    def analyze(self, expression: str) -> DaxDependencies:
        """Analiza una expresión DAX y devuelve sus dependencias."""
        deps = DaxDependencies()
        if not expression:
            return deps

        # Remove lineageTag and other metadata that may appear after the expression
        expression = self._clean_expression(expression)

        # Strip comments first
        text = _RE_BLOCK_COMMENT.sub(' ', expression)
        text = _RE_LINE_COMMENT.sub(' ', text)

        # 1) Extract quoted table[col] references  'My Table'[Col]
        for m in _RE_QUOTED_TABLE_COL.finditer(text):
            tbl, col = m.group(1).strip(), m.group(2).strip()
            tbl_resolved = self._resolve_table(tbl)
            deps.add_column(tbl_resolved, col)

        # Remove quoted refs so they don't interfere
        text_no_quoted = _RE_QUOTED_TABLE_COL.sub(' ', text)

        # 2) Extract unquoted table[col] references  Table[Col]
        for m in _RE_UNQUOTED_TABLE_COL.finditer(text_no_quoted):
            tbl_raw, col = m.group(1).strip(), m.group(2).strip()
            tbl = self._resolve_table(tbl_raw)
            deps.add_column(tbl, col)

        # 3) Remove all table[col] patterns so remaining [X] are measures
        text_no_refs = _RE_UNQUOTED_TABLE_COL.sub(' ', text_no_quoted)
        text_no_refs = re.sub(r"'[^']+'\s*\[[^\]]+\]", ' ', text_no_refs)

        # 4) Standalone [Measure] references
        for m in re.finditer(r'\[([^\]]+)\]', text_no_refs):
            ref = m.group(1).strip()
            # Check if it's a known measure
            if ref.lower() in self._measures_lower:
                deps.measures.add(self._measures_lower[ref.lower()])
            else:
                # Could be a column of the current table or an unknown measure
                deps.measures.add(ref)

        # 5) Functions – words followed by (
        for m in re.finditer(r'\b([A-Za-z_][\w.]*)\s*\(', text):
            fname = m.group(1).upper()
            if fname in DAX_FUNCTIONS:
                deps.functions.add(fname)

        # 6) Variables – VAR name = ...
        for m in re.finditer(r'\bVAR\s+(\w+)', text, re.IGNORECASE):
            deps.variables.add(m.group(1))

        return deps

    # ──────────────────────────────────────────
    # Public: analyze all measures
    # ──────────────────────────────────────────

    def analyze_all_measures(
        self,
        measures: Optional[Dict[str, str]] = None,
    ) -> Dict[str, DaxDependencies]:
        """
        Analiza todas las medidas y devuelve un diccionario {nombre: deps}.

        Args:
            measures: Dict {measure_name: expression}. Si es None, usa
                      self.known_measures.
        """
        measures = measures or self.known_measures
        results: Dict[str, DaxDependencies] = {}
        for name, expr in measures.items():
            results[name] = self.analyze(expr)
        return results

    # ──────────────────────────────────────────
    # Public: transitive resolution
    # ──────────────────────────────────────────

    def resolve_transitive_measures(
        self,
        all_deps: Dict[str, DaxDependencies],
    ) -> Dict[str, DaxDependencies]:
        """
        Resuelve dependencias transitivas de medidas.

        Si medida A usa [B] y B usa Table[Col] y [C], al resolver A
        se añaden también las dependencias de B y C (recursivamente).

        Detecta ciclos para evitar recursión infinita.

        Returns:
            Diccionario con las mismas claves pero deps expandidas.
        """
        resolved: Dict[str, DaxDependencies] = {}
        resolving: Set[str] = set()  # cycle detection

        def _resolve(name: str) -> DaxDependencies:
            if name in resolved:
                return resolved[name]
            if name not in all_deps:
                return DaxDependencies()
            if name in resolving:
                # Cycle detected – return what we have
                return all_deps[name]

            resolving.add(name)
            base = all_deps[name]
            merged = DaxDependencies(
                tables=set(base.tables),
                columns={t: set(cols) for t, cols in base.columns.items()},
                measures=set(base.measures),
                functions=set(base.functions),
                variables=set(base.variables),
            )

            for measure_ref in list(base.measures):
                child = _resolve(measure_ref)
                merged.tables |= child.tables
                for t, cols in child.columns.items():
                    merged.columns.setdefault(t, set()).update(cols)
                merged.measures |= child.measures
                merged.functions |= child.functions
                # Don't merge variables – they are local

            resolving.discard(name)
            resolved[name] = merged
            return merged

        for name in all_deps:
            _resolve(name)

        return resolved

    # ──────────────────────────────────────────
    # Public: table dependency graph
    # ──────────────────────────────────────────

    def get_table_dependencies(
        self,
        all_deps: Dict[str, DaxDependencies],
        measure_table_map: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Set[str]]:
        """
        Para cada tabla, devuelve el conjunto de otras tablas de las que depende
        (a través de sus medidas).

        Args:
            all_deps: resultado de analyze_all_measures o resolve_transitive_measures
            measure_table_map: {measure_name: table_name} – tabla donde vive cada medida

        Returns:
            {tabla: {tablas de las que depende}}
        """
        table_deps: Dict[str, Set[str]] = {}
        measure_table_map = measure_table_map or {}

        for measure_name, deps in all_deps.items():
            owner_table = measure_table_map.get(measure_name)
            if not owner_table:
                continue
            table_deps.setdefault(owner_table, set())
            for ref_table in deps.tables:
                if ref_table != owner_table:
                    table_deps[owner_table].add(ref_table)

        return table_deps

    # ──────────────────────────────────────────
    # Public: ensure dependencies table exists
    # ──────────────────────────────────────────

    @staticmethod
    def ensure_dependencies_table(conn) -> None:
        """
        Crea la tabla ``semantic_model_measure_dependencies`` si no existe.

        Útil para garantizar que la tabla exista (aunque vacía) antes de que
        otros métodos como ``create_subset_model_from_db`` la consulten.

        Args:
            conn: Conexión DuckDB abierta (read-write).
        """
        conn.execute(
            "CREATE SEQUENCE IF NOT EXISTS seq_sm_measure_dep_id START 1"
        )
        conn.execute("""
            CREATE TABLE IF NOT EXISTS semantic_model_measure_dependencies (
                id INTEGER PRIMARY KEY DEFAULT nextval('seq_sm_measure_dep_id'),
                semantic_model_id INTEGER NOT NULL,
                measure_name VARCHAR NOT NULL,
                measure_table VARCHAR NOT NULL,
                dependency_type VARCHAR NOT NULL,
                referenced_name VARCHAR NOT NULL,
                referenced_table VARCHAR,
                created_at TIMESTAMP DEFAULT now(),
                FOREIGN KEY(semantic_model_id) REFERENCES semantic_model(id)
            )
        """)

    # ──────────────────────────────────────────
    # Public: save dependencies to DuckDB
    # ──────────────────────────────────────────

    def save_dependencies_to_db(
        self,
        db_path: str,
        semantic_model_id: Optional[int] = None,
        measure_table_map: Optional[Dict[str, str]] = None,
        conn=None,
    ) -> int:
        """
        Calcula las dependencias transitivas de todas las medidas y las
        guarda en ``semantic_model_measure_dependencies``.

        Cada fila representa una dependencia individual con su tipo:

        * **measure** – la medida referencia a otra medida.
        * **table** – la medida accede a una tabla (vía ``Table[Col]``).
        * **column** – la medida accede a una columna específica.

        Args:
            db_path: Ruta al fichero .duckdb.
            semantic_model_id: ID numérico del modelo. Si None, usa el primero.
            measure_table_map: {measure_name: table_name} indicando en qué tabla
                vive cada medida.  Si None se infiere desde la DB.

        Returns:
            Número de filas insertadas.
        """
        import duckdb

        _own_conn = conn is None
        if _own_conn:
            conn = duckdb.connect(db_path)
        try:
            # Resolver semantic_model_id
            if semantic_model_id is None:
                row = conn.execute(
                    "SELECT id FROM semantic_model LIMIT 1"
                ).fetchone()
                if not row:
                    raise ValueError("No semantic models found in database")
                semantic_model_id = row[0]

            # Si no nos pasan measure_table_map, cargarlo de la DB
            if measure_table_map is None:
                rows = conn.execute(
                    "SELECT measure_name, table_name FROM semantic_model_measure "
                    "WHERE semantic_model_id = ?",
                    [semantic_model_id],
                ).fetchall()
                measure_table_map = {r[0]: r[1] for r in rows}

            # Calcular dependencias transitivas
            all_deps = self.analyze_all_measures()
            resolved = self.resolve_transitive_measures(all_deps)

            # Crear tabla + secuencia (reutiliza ensure_dependencies_table)
            DaxTokenizer.ensure_dependencies_table(conn)

            # Limpiar datos anteriores de este modelo
            conn.execute(
                "DELETE FROM semantic_model_measure_dependencies "
                "WHERE semantic_model_id = ?",
                [semantic_model_id],
            )

            # Construir filas a insertar
            rows_to_insert: List[Tuple] = []

            for measure_name, deps in resolved.items():
                owner_table = measure_table_map.get(measure_name, "")

                # Dependencias tipo "table"
                for tbl in sorted(deps.tables):
                    rows_to_insert.append((
                        semantic_model_id,
                        measure_name,
                        owner_table,
                        "table",
                        tbl,
                        None,
                    ))

                # Dependencias tipo "column"
                for tbl, cols in sorted(deps.columns.items()):
                    for col in sorted(cols):
                        rows_to_insert.append((
                            semantic_model_id,
                            measure_name,
                            owner_table,
                            "column",
                            col,
                            tbl,
                        ))

                # Dependencias tipo "measure"
                for mref in sorted(deps.measures):
                    ref_table = measure_table_map.get(mref, "")
                    rows_to_insert.append((
                        semantic_model_id,
                        measure_name,
                        owner_table,
                        "measure",
                        mref,
                        ref_table,
                    ))

            # Insertar en batch
            if rows_to_insert:
                conn.executemany(
                    "INSERT INTO semantic_model_measure_dependencies "
                    "(semantic_model_id, measure_name, measure_table, "
                    " dependency_type, referenced_name, referenced_table) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    rows_to_insert,
                )

            return len(rows_to_insert)

        finally:
            if _own_conn:
                conn.close()

    # ──────────────────────────────────────────
    # Classmethod: from DuckDB
    # ──────────────────────────────────────────

    @classmethod
    def from_duckdb(
        cls,
        db_path: str,
        semantic_model_id: Optional[int] = None,
        conn=None,
    ) -> Tuple['DaxTokenizer', Dict[str, str]]:
        """
        Carga contexto del modelo desde DuckDB y crea una instancia.

        Args:
            db_path: Ruta al fichero .duckdb.
            semantic_model_id: ID del modelo. Si None, usa el primer modelo encontrado.

        Returns:
            Tuple (DaxTokenizer, measure_table_map) donde measure_table_map es
            {measure_name: table_name}.
        """
        import duckdb

        _own_conn = conn is None
        if _own_conn:
            conn = duckdb.connect(db_path, read_only=True)
        try:
            # Get model id
            if semantic_model_id is None:
                row = conn.execute(
                    "SELECT id FROM semantic_model LIMIT 1"
                ).fetchone()
                if not row:
                    raise ValueError("No semantic models found in database")
                semantic_model_id = row[0]

            # Load tables
            tables_rows = conn.execute(
                "SELECT DISTINCT table_name FROM semantic_model_table WHERE semantic_model_id = ?",
                [semantic_model_id],
            ).fetchall()
            known_tables = {r[0] for r in tables_rows}

            # Load columns
            col_rows = conn.execute(
                "SELECT table_name, column_name FROM semantic_model_column WHERE semantic_model_id = ?",
                [semantic_model_id],
            ).fetchall()
            known_columns: Dict[str, Set[str]] = {}
            for tbl, col in col_rows:
                known_columns.setdefault(tbl, set()).add(col)

            # Load measures
            meas_rows = conn.execute(
                "SELECT table_name, measure_name, expression FROM semantic_model_measure WHERE semantic_model_id = ?",
                [semantic_model_id],
            ).fetchall()
            known_measures: Dict[str, str] = {}
            measure_table_map: Dict[str, str] = {}
            for tbl, mname, expr in meas_rows:
                known_measures[mname] = expr or ""
                measure_table_map[mname] = tbl

            return cls(known_tables, known_measures, known_columns), measure_table_map

        finally:
            if _own_conn:
                conn.close()

    # ──────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────

    def _resolve_table(self, name: str) -> str:
        """Return the canonical table name (case-insensitive match)."""
        low = name.lower()
        if low in self._tables_lower:
            return self._tables_lower[low]
        return name

    @staticmethod
    def _clean_expression(expr: str) -> str:
        """
        Remove lineageTag and other metadata lines that are appended
        to measure expressions in some TMDL formats.
        """
        lines = expr.split('\n')
        clean_lines = []
        for line in lines:
            stripped = line.strip().lower()
            if stripped.startswith('lineagetag:'):
                break
            if stripped.startswith('changedproperty'):
                break
            if stripped.startswith('formatstring:'):
                break
            clean_lines.append(line)
        return '\n'.join(clean_lines)
