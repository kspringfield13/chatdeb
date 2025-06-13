#!/usr/bin/env python3
# drop_all.py

import os
import duckdb

# Path to your DuckDB file.  The chatbot now uses the ingested database by
# default so we drop tables/views from that location.
DB_PATH = os.path.join(os.path.dirname(__file__), "../ingested_data/ingest.db")

def drop_all_tables_and_views(db_path: str):
    """
    Connects to the DuckDB at db_path, finds all tables and views in the 'main' schema,
    and drops each one.
    """
    con = duckdb.connect(db_path)

    # Query to list all tables and views in the 'main' schema
    qry = """
    SELECT table_name, table_type
    FROM information_schema.tables
    WHERE table_schema = 'main';
    """
    results = con.execute(qry).fetchall()

    for table_name, table_type in results:
        # DuckDB uses 'BASE TABLE' for actual tables, 'VIEW' for views
        if table_type.upper() == "VIEW":
            drop_stmt = f'DROP VIEW IF EXISTS "{table_name}";'
        else:  # BASE TABLE
            drop_stmt = f'DROP TABLE IF EXISTS "{table_name}";'

        try:
            con.execute(drop_stmt)
            print(f"🔹 Dropped {table_type.lower()} '{table_name}'")
        except Exception as e:
            print(f"❌ Error dropping {table_type.lower()} '{table_name}': {e}")

    con.close()
    print("\n✅ All tables and views dropped.")

if __name__ == "__main__":
    if not os.path.isfile(DB_PATH):
        print(f"Error: DuckDB file not found at {DB_PATH}")
    else:
        drop_all_tables_and_views(DB_PATH)