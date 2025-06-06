import os
from ..infograph import generate_infograph_questions, create_infographic


def test_questions_start_with_intro():
    qs = generate_infograph_questions([])
    assert qs
    assert qs[0].startswith("To create your infographic")


def test_create_infographic_file(tmp_path):
    path = create_infographic(["Demo Title", "123"])
    assert path.endswith(".png")
    assert os.path.exists(path)


