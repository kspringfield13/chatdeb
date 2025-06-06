import pytest
from ..chatbot import is_data_question

@pytest.mark.parametrize("q", [
    "How many orders did we ship last month?",
    "Show me the top 10 customers by revenue.",
    "What's the average order value?",
    "List employees with more than 5 sales this quarter."
])
def test_positive(q):
    assert is_data_question(q)

@pytest.mark.parametrize("q", [
    "Tell me about your return policy.",
    "How do I reset my password?"
])
def test_negative(q):
    assert not is_data_question(q)
