import os
import re
import pytest
from pathlib import Path

from ..visualize import (
    generate_context_questions,
    infer_headers,
    create_table_visual,
    create_matplotlib_visual,
)


def test_default_intro_included():
    qs = generate_context_questions([])
    assert qs, "No questions returned"
    assert qs[0].startswith("To create a visualization for you"), qs[0]


def test_generate_context_questions_length():
    qs = generate_context_questions([])
    assert len(qs) == 4


def test_generate_context_questions_last_table():
    history = [
        {"sender": "bot", "text": "Here is your table:", "image": "/charts/table_x.png", "data": "/charts/table_x.txt"}
    ]
    qs = generate_context_questions(history)
    assert len(qs) == 4
    assert "x-axis" in qs[0].lower()


def test_infer_headers_typing():
    rows = [
        (123, "abc", "2024-01-01"),
        (456, "def", "2024-02-01"),
    ]
    assert infer_headers(rows) == ["Number 1", "Text 2", "Date 3"]


def test_create_table_visual_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = create_table_visual([(1, "a"), (2, "b")])
    assert path.endswith(".png")
    assert os.path.exists(path)
    txt = Path(path).with_suffix(".txt")
    assert txt.exists()
    assert txt.read_text()


def test_create_table_visual_headers(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = create_table_visual([(1, 2)], headers=["id", "value"])
    txt = Path(path).with_suffix(".txt")
    assert txt.read_text().splitlines()[0] == "Id,Value"


def test_create_matplotlib_visual_from_table(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    png = create_table_visual([(1, 2)], headers=["a", "b"])
    txt = Path(png).with_suffix(".txt")
    path = create_matplotlib_visual([str(txt), "A", "B", "bar"])
    assert Path(path).exists()


def test_generate_context_questions_fallback(monkeypatch):
    class DummyClient:
        class Chat:
            class Completions:
                @staticmethod
                def create(*args, **kwargs):
                    return type(
                        "Resp",
                        (),
                        {
                            "choices": [
                                type(
                                    "C",
                                    (),
                                    {
                                        "message": type(
                                            "M", (), {"content": "Not questions"}
                                        )()
                                    },
                                )
                            ]
                        },
                    )()

        chat = Chat()

    monkeypatch.setattr("kydxbot.visualize.OpenAI", lambda: DummyClient())
    qs = generate_context_questions([{"sender": "user", "text": "Hello"}])
    assert qs[0].startswith("To create a visualization for you")
    assert len(qs) == 4


def test_create_matplotlib_visual_invalid_sql(monkeypatch):
    with pytest.raises(ValueError):
        create_matplotlib_visual(["missing.csv", "x", "y", "bar"])
