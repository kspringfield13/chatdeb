import os
from pathlib import Path
from PIL import Image

from kydxbot.directorscut import generate_directors_cut


def test_generate_directors_cut(tmp_path, monkeypatch):
    img = Image.new("RGB", (200, 100), color="blue")
    table_path = tmp_path / "table.png"
    img.save(table_path)
    history = [{"sender": "bot", "text": "Here is your table:", "image": str(table_path)}]
    monkeypatch.chdir(tmp_path)
    path = generate_directors_cut(history)
    assert path.endswith(".mp4")
    assert os.path.exists(path)
