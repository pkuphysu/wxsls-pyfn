import pytest
from _pytest.monkeypatch import MonkeyPatch

from pkuphysu_wechat import create_app, db, settings

from .utils import Client


@pytest.fixture(scope="class")
def client():
    app = create_app()
    app.test_client_class = Client
    with app.app_context():
        db.create_all()
        db.session.commit()
        with app.test_client() as client:
            yield client
        db.session.close()
        db.drop_all()


@pytest.fixture(scope="class")
def master_access():
    mpatch = MonkeyPatch()
    mpatch.setitem(settings["WECHAT"], "MASTER_IDS", "developmentopenid")
    yield
    mpatch.undo()


def pytest_runtest_makereport(item, call):
    if "incremental" in item.keywords:
        if call.excinfo is not None:
            parent = item.parent
            parent._previousfailed = item


def pytest_runtest_setup(item):
    previousfailed = getattr(item.parent, "_previousfailed", None)
    if previousfailed is not None:
        pytest.xfail("prevfail [%s]" % previousfailed.name)
