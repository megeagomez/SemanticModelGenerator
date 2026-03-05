from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import duckdb
from typing import List, Optional

app = FastAPI()

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DUCKDB_DIR = Path("data")

@app.get("/workspaces")
def list_workspaces() -> List[str]:
    """List available DuckDB workspace files."""
    dbs = [str(p) for p in DUCKDB_DIR.glob("*.duckdb")]
    return dbs

@app.get("/reports")
def list_reports(db_path: str = Query(...)) -> List[str]:
    """List reports in a DuckDB workspace."""
    con = duckdb.connect(db_path, read_only=True)
    reports = con.execute("SELECT DISTINCT name FROM report").fetchall()
    con.close()
    return [r[0] for r in reports]

@app.get("/models")
def list_models(db_path: str = Query(...)) -> List[str]:
    """List semantic models in a DuckDB workspace."""
    con = duckdb.connect(db_path, read_only=True)
    models = con.execute("SELECT DISTINCT name FROM semanticmodel").fetchall()
    con.close()
    return [m[0] for m in models]

@app.get("/report_details")
def get_report_details(db_path: str = Query(...), report_name: str = Query(...)):
    """Get details for a report (pages, tables, visuals, etc)."""
    con = duckdb.connect(db_path, read_only=True)
    # Example: get pages
    pages = con.execute("SELECT name FROM page WHERE report_name = ?", [report_name]).fetchall()
    con.close()
    return {"pages": [p[0] for p in pages]}

@app.get("/model_details")
def get_model_details(db_path: str = Query(...), model_name: str = Query(...)):
    """Get details for a semantic model (tables, measures, etc)."""
    con = duckdb.connect(db_path, read_only=True)
    tables = con.execute("SELECT name FROM table WHERE semanticmodel_name = ?", [model_name]).fetchall()
    con.close()
    return {"tables": [t[0] for t in tables]}
