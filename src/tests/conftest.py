import os

import pytest
from _pytest.monkeypatch import MonkeyPatch

os.environ["ENV_FOR_DYNACONF"] = "testing"


@pytest.fixture(scope="class")
def client():
    from pkuphysu_wechat import create_app, db

    from .utils import Client

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
    from pkuphysu_wechat import settings

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


def pytest_ignore_collect(path):
    from pkuphysu_wechat.api import modules

    if path.isdir():
        parent_path = path.parts()[-2]
        if parent_path.purebasename == "api" and path.purebasename not in modules:
            return True
