from types import SimpleNamespace

from werobot.client import ClientException

from pkuphysu_wechat.wechat import wechat_client


def test_code_correct(client, monkeypatch):
    data = SimpleNamespace()
    data.called = 0

    def mock_oauth(*_):
        data.called += 1
        return {"openid": "OPENID"}

    monkeypatch.setattr(wechat_client, "oauth", mock_oauth)
    rv = client.get("/auth/wechat?code=233333")
    assert "token" in rv.json
    assert data.called == 1


def test_code_wrong(client, monkeypatch):
    def mock_oauth(_):
        raise ClientException("hahaha")

    monkeypatch.setattr(wechat_client, "oauth", mock_oauth)
    rv = client.get("/auth/wechat?code=233333")
    assert rv.json.get("errid") == "AuthBadCode"


def test_auth_exsisting_token(client):
    # In browser
    rv = client.get("/auth/tcode/get")
    tcode = rv.json.get("tcode")
    assert rv.status_code == 200
    assert tcode
    # In wechat
    rv = client.get(
        f"/auth/tcode/grant?tcode={tcode}",
        headers=[("Authorization", "Basic developmentoken")],
    )
    assert rv.status_code == 200
    # In browser
    rv = client.get(f"/auth/tcode/exchange?tcode={tcode}")
    token = rv.json.get("token")
    assert token


def test_dev_token(client):
    rv = client.get(
        "/auth/openid",
        headers=[("Authorization", "Basic developmentoken")],
    )
    assert rv.status_code == 200
    assert rv.json.get("openid") == "developmentopenid"
