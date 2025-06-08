import os
import re
import pytest
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
    with pytest.raises(ValueError) as exc:
        create_matplotlib_visual(["table", "x", "y", "bar"])
    assert "SELECT" in str(exc.value)
