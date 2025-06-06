import pytest
from kydxbot.detection import is_data_question, is_db_path_question

@pytest.mark.parametrize("q", [
    "How many orders did we ship last month?",
    "Show me the top 10 customers by revenue.",
    "What's the average order value?",
    "List employees with more than 5 sales this quarter.",
    "Show me the database schema.",
    "What datasets are loaded?",
    "Analyze the duckdb data."
])
def test_positive(q):
    assert is_data_question(q)

@pytest.mark.parametrize("q", [
    "Tell me about your return policy.",
    "How do I reset my password?"
])
def test_negative(q):
    assert not is_data_question(q)


@pytest.mark.parametrize("q", [
    "What is the database path?",
    "Where is your db located?",
    "Provide the full path to the database file",
])
def test_db_path_positive(q):
    assert is_db_path_question(q)


@pytest.mark.parametrize("q", [
    "How many orders did we ship?",
    "Tell me about your return policy.",
])
def test_db_path_negative(q):
    assert not is_db_path_question(q)
