# db.py

import os
from pathlib import Path
import duckdb
from sqlalchemy import create_engine

# Default database used across the application.  Historically this lived under
# ``data/data.db`` but all processes now work exclusively with the ingested
# dataset in ``ingested_data/ingest.db``.
DEFAULT_DB_PATH = Path(__file__).resolve().parent / "ingested_data" / "ingest.db"
# Backwards compat constant
DUCKDB_PATH = str(DEFAULT_DB_PATH)


def _get_path() -> str:
    """Return the DuckDB file path, allowing ``DUCKDB_PATH`` env override."""
    return os.getenv("DUCKDB_PATH", str(DEFAULT_DB_PATH))


def get_engine():
    """Return a new SQLAlchemy engine for the current DuckDB path."""
    path = _get_path()
    return create_engine(f"duckdb:///{path}?access_mode=read_write")


def get_duckdb_connection():
    """Return a new DuckDB connection for the current path."""
    path = _get_path()
    return duckdb.connect(path)
