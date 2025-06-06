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
