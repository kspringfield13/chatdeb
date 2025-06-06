import os
import json

os.environ["KYDXBOT_TESTING"] = "1"

from kydxbot.chatbot import load_recent_history


def test_load_history_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert load_recent_history() == []


def test_load_history_reads_last_entries(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data = [
        {"query_text": f"q{i}", "retrieved_response": f"r{i}"} for i in range(5)
    ]
    with open("chatbot_responses.json", "w", encoding="utf-8") as f:
        json.dump(data, f)
    hist = load_recent_history(3)
    assert [d["query_text"] for d in hist] == ["q2", "q3", "q4"]
