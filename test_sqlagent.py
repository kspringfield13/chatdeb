# test_sqlagent.py

import pytest
pytest.skip(
    "SQL agent tests require database and API keys", allow_module_level=True
)

from langchain_sql import query_via_sqlagent

questions = [
    "List the top 5 products by profit.",
    "Which customers have more than 3 web_sessions?",
    "What is the total sales_amount for category 'Accessories'?",
    "Which products have a profit margin below $10?",
    "How many customers are from United States?",
    "Who are my best customers right now?",
    "Which products have the smallest profit margin?"
]

for q in questions:
    print(f"\nQ: {q}")
    answer = query_via_sqlagent(q)
    print(f"A:\n{answer}")