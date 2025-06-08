from ..erd import generate_erd, get_data_summary, describe_erd
import os


def test_summary_not_empty():
    text = get_data_summary()
    assert isinstance(text, str)
    assert text


def test_generate_erd_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = generate_erd()
    assert path.endswith(".png")
    assert os.path.exists(path)


def test_describe_erd_handles_error(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Create a dummy image
    path = generate_erd()

    class DummyClient:
        class Chat:
            class Completions:
                @staticmethod
                def create(*args, **kwargs):
                    return type("Resp", (), {"choices": [type("C", (), {"message": type("M", (), {"content": "desc"})()})]})()

        chat = Chat()

    monkeypatch.setattr("kydxbot.erd.OpenAI", lambda: DummyClient())
    text = describe_erd(path)
    assert isinstance(text, str)

