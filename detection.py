from __future__ import annotations

from .preloaded_questions import is_similar


def is_data_question(query_text: str) -> bool:
    """Return ``True`` if ``query_text`` looks like a data analysis request."""
    q = query_text.lower()
    keywords = [
        "average", "sum(", "count(", "how many", "what is", "list",
        "top", "highest", "lowest", "per", "between", "profit",
        "sales", "customers", "products", "revenue", "orders",
        "invoices", "inventory", "expenses", "transactions", "employees",
        "payroll", "income", "metrics",
        "database", "duckdb", "dataset", "datasets", "db", "my db", "my database", "my data",
        "loaded data", "ingested data", "imported data", "shared data", "the data",
        "my datasets", "my dataset", "this data", "the tables", "my tables",
    ]

    if any(kw in q for kw in keywords):
        return True

    try:
        return is_similar(query_text)
    except Exception:
        return False


def is_db_path_question(query_text: str) -> bool:
    """Return True if the user is asking for the database file location."""
    q = query_text.lower()
    keywords = [
        "db path",
        "database path",
        "path to database",
        "where is the database",
        "database location",
        "path to db",
        "where is your db",
        "file path",
        "database file",
    ]
    return any(kw in q for kw in keywords)
