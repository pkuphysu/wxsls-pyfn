import pytest

from pkuphysu_wechat import create_app, db


@pytest.fixture(scope="class")
def client():
    app = create_app()
    with app.app_context():
        db.create_all()
        db.session.commit()
        with app.test_client() as client:
            yield client
        db.session.close()
        db.drop_all()
