from .utils import mock_exec


def test_work():
    assert "help" in mock_exec("help")
