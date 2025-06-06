def is_data_question(query_text: str) -> bool:
    """Lightweight helper used by tests. Checks if query hints at needing data."""
    q = query_text.lower()
    keywords = [
        "average", "sum(", "count(", "how many", "what is", "list",
        "top", "highest", "lowest", "per", "between", "profit",
        "sales", "customers", "products", "revenue", "orders",
        "invoices", "inventory", "expenses", "transactions", "employees",
        "payroll", "income", "metrics",
        # Treat generic references to the data as data questions as well
        "database", "duckdb", "dataset", "datasets", "db", "my db", "my database", "my data"
        "loaded data", "uploaded data", "imported data", "shared data", "the data", 
        "my datasets", "my dataset", "this data", "the tables", "my tables"
    ]
    return any(kw in q for kw in keywords)


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
