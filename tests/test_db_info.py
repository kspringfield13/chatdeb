import os
import asyncio
os.environ["KYDXBOT_TESTING"] = "1"
from kydxbot.server import db_info

def test_db_info_size():
    info = asyncio.run(db_info())
    assert isinstance(info.size, int)
    assert info.size > 0
