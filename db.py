# db.py

import os
import duckdb
from sqlalchemy import create_engine

DUCKDB_PATH = os.path.join(os.path.dirname(__file__), "data", "data.db")

_engine = None
_connection = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(f"duckdb:///{DUCKDB_PATH}?access_mode=read_write")
    return _engine

def get_duckdb_connection():
    global _connection
    if _connection is None:
        _connection = duckdb.connect(DUCKDB_PATH)
    return _connection
