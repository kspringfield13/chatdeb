def is_data_question(query_text: str) -> bool:
    """Return ``True`` if a question is data-centric."""
    q = query_text.lower()
    data_keywords = [
        "average",
        "sum(",
        "count(",
        "how many",
        "what is",
        "list",
        "top",
        "highest",
        "lowest",
        "per",
        "between",
        "profit",
        "sales",
        "customers",
        "products",
        "revenue",
        "orders",
        "invoices",
        "inventory",
        "expenses",
        "transactions",
        "employees",
        "payroll",
        "income",
        "metrics",
    ]
    return any(kw in q for kw in data_keywords)
