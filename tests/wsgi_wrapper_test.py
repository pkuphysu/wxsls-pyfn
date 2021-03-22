import json
from pathlib import Path

import pytest

from pkuphysu_wechat.wsgi_wrapper import main


@pytest.mark.parametrize("filename", ["get.json", "post.json"])
def test_work(filename):
    with open(Path(__file__).parent / "data" / filename) as f:
        event = json.load(f)
    result = main(event, None)
    assert result["body"] == "12314"
    assert result["statusCode"] == 200
