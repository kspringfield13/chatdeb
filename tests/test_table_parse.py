import re
from kydxbot.chatbot import _maybe_convert_text_table

def test_extract_embedded_table_path():
    text = "Explanation before\nTABLE:charts/foo.png"
    assert _maybe_convert_text_table(text) == "TABLE:charts/foo.png"

