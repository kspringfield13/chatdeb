import asyncio
import os
import duckdb
import pytest

os.environ["KYDXBOT_TESTING"] = "1"

from kydxbot import server



def test_ingest_sample_dataset1(tmp_path, monkeypatch):
    db_path = tmp_path / "ingest.db"
    monkeypatch.setattr(server, "INGEST_DIR", tmp_path)
    monkeypatch.setattr(server, "INGEST_DB_PATH", db_path)
    monkeypatch.setattr("kydxbot.config.INGEST_DIR", tmp_path)
    monkeypatch.setattr("kydxbot.config.INGEST_DB_PATH", db_path)

    asyncio.run(server.ingest_sample("dataset1"))

    assert db_path.exists()
    con = duckdb.connect(str(db_path))
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    expected = {"raw_orders", "raw_order_items", "raw_products"}
    assert expected.issubset(tables)
    for t in expected:
        count = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        assert count > 0
    con.close()


