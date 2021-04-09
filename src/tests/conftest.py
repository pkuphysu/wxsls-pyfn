import pytest

from pkuphysu_wechat import create_app


@pytest.fixture(scope="class")
def app():
    app = create_app()
    yield app


@pytest.fixture(scope="class")
def client(app):
    with app.test_client() as client:
        yield client
