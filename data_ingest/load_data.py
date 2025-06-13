# data_ingest/load_data.py

from __future__ import annotations

import os
from pathlib import Path
import duckdb
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
DUCKDB_PATH = ROOT / "data" / "data.db"

# Location of the raw files to load
RAW_DIR = ROOT / "raw_data"

def ingest_table(con: duckdb.DuckDBPyConnection, table_name: str, file_name: str):
    """
    Drops & recreates a staging table in DuckDB from a CSV, Excel, or JSON file.
    """
    full_path = RAW_DIR / file_name

    if not full_path.is_file():
        print(f"⚠️  {file_name} not found, skipping")
        return

    # Determine the file type and read accordingly
    try:
        if full_path.suffix.lower() == ".csv":
            df = pd.read_csv(full_path)
        elif full_path.suffix.lower() in {".xls", ".xlsx"}:
            df = pd.read_excel(full_path)
        elif full_path.suffix.lower() == ".json":
            df = pd.read_json(full_path, orient="records", lines=False)
        else:
            print(f"⚠️  Unsupported file type for {file_name}, skipping")
            return
    except Exception as exc:
        print(f"❌ Failed to load {file_name}: {exc}")
        return

    # Drop if exists, then create
    con.execute(f"DROP TABLE IF EXISTS {table_name};")
    con.register("tmp_df", df)
    con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM tmp_df;")
    con.unregister("tmp_df")

    print(f"⬢ Ingested {table_name} ({len(df)} rows) from {file_name}")

def main():
    DUCKDB_PATH.parent.mkdir(exist_ok=True)
    con = duckdb.connect(str(DUCKDB_PATH))

    # Example mapping: staging_table_name → filename.csv
    table_files = {
        "raw_events":               "raw_events.csv",
        "raw_inventory_items":      "raw_inventory_items.csv",
        "raw_order_items":          "raw_order_items.csv",
        "raw_orders":               "raw_orders.csv",
        "raw_products":             "raw_products.csv",
        "raw_users":                "raw_users.csv",
        # …add any others you have…
    }

    # Ingest each table
    for table_name, file_name in table_files.items():
        ingest_table(con, table_name, file_name)

    print("✅ All ecommerce staging tables loaded.\n")

    # QA CHECK: Log row counts for each loaded table
    print("🔍 QA: Verifying row counts for each table...")
    for table_name in table_files.keys():
        try:
            result = con.execute(f"SELECT COUNT(*) FROM {table_name};").fetchone()
            row_count = result[0] if result else 0
            print(f"   • {table_name}: {row_count} rows")
        except Exception as e:
            print(f"   • {table_name}: ERROR checking row count ({e})")

    con.close()
    print("\n✅ QA complete. Connection closed.")

    # ── Additional step: extract dataset metadata using OpenAI Vision ──
    try:
        from pathlib import Path
        from .vision_metadata import generate_metadata

        generate_metadata(Path(RAW_DIR))
        print("✅ Metadata extracted with vision\n")
    except Exception as e:  # noqa: BLE001
        print("⚠️ Vision metadata step failed", e)

if __name__ == "__main__":
    main()
