import os
import pytest
os.environ["KYDXBOT_TESTING"] = "1"
from kydxbot import chatbot


def test_find_metadata_matches(monkeypatch):
    meta = {"sales.csv": {"headers": ["Revenue", "Month"], "summary": ""}}
    monkeypatch.setattr(chatbot, "VISION_METADATA", meta)
    matches = chatbot._find_metadata_matches("Show revenue trends by month")
    assert "sales.Revenue" in matches
