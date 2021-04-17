from pkuphysu_wechat import settings


def test_db_create(client):
    rv = client.get(f"/tasks/db/create?token={settings.TASK_AUTH_TOKEN}")
    assert b"DB Created" in rv.data
