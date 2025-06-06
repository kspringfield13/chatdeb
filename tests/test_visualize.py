import re
from ..visualize import generate_context_questions


def test_default_intro_included():
    qs = generate_context_questions([])
    assert qs, "No questions returned"
    assert qs[0].startswith("To create your visualization"), qs[0]
