from ..erd import generate_erd, get_data_summary
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

