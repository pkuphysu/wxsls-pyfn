from unittest.mock import MagicMock

import pytest

from pkuphysu_wechat.wechat_manager import core, views
from pkuphysu_wechat.wechat_manager.models import WechatLoginSession, WechatSession

FINGERPRINT = "0123456789abcdef0123456789abcdef"
HEAD_IMG_URL = "https://wx.qlogo.cn/mmopen/abc/64"


@pytest.fixture()
def fake_mp(monkeypatch):
    """Replace every outbound mp.weixin.qq.com call with in-memory fakes.

    The returned ``state`` dict lets each test script the protocol answers.
    """
    state = {
        "startlogin_ret": 0,
        "ask": {"base_resp": {"ret": 0}, "status": 0},
        "login": {
            "base_resp": {"ret": 0},
            "redirect_url": "https://mp.weixin.qq.com/cgi-bin/home"
            "?t=home/index&lang=zh_CN&token=1234567890",
        },
        "check_home": True,
        "head_img_url": HEAD_IMG_URL,
    }

    def make_fake_session():
        return MagicMock()

    class FakeMpClient:
        def __init__(self, session, fingerprint, token="", user_agent=""):
            self.session = session
            self.fingerprint = fingerprint
            self.token = token

        def prelogin(self):
            return {}

        def startlogin(self, sessionid):
            return {"base_resp": {"ret": state["startlogin_ret"]}}

        def get_qrcode(self):
            return b"fakeqrcode"

        def ask(self):
            return state["ask"]

        def login(self):
            return state["login"]

        def get_fans_info(self, openid):
            if state["head_img_url"] is None:
                return None
            return state["head_img_url"]

        def check_home(self):
            if state["check_home"] is None:
                raise core.requests.RequestException("network down")
            return state["check_home"]

    monkeypatch.setattr(views, "MpClient", FakeMpClient)
    monkeypatch.setattr(views, "new_session", lambda user_agent="": make_fake_session())
    monkeypatch.setattr(
        views,
        "client_for_login_row",
        lambda row: FakeMpClient(make_fake_session(), row.fingerprint),
    )
    monkeypatch.setattr(core, "MpClient", FakeMpClient)
    monkeypatch.setattr(
        core,
        "client_from_session_row",
        lambda row: FakeMpClient(
            make_fake_session(), row.fingerprint, row.token, row.user_agent
        ),
    )
    state["qrcode"] = "data:image/jpeg;base64," + b64encode_str(b"fakeqrcode")
    return state


def b64encode_str(data: bytes) -> str:
    import base64

    return base64.b64encode(data).decode("ascii")


def db_get_login(login_id):
    from pkuphysu_wechat import db

    return db.session.get(WechatLoginSession, login_id)


def test_login_start_requires_fingerprint(client):
    rv = client.open_with_token("/wechat-manager/login/start", method="POST", json={})
    assert rv.status_code == 400
    assert rv.json.get("errid") == "MpLoginFingerprintInvalid"


def test_login_start_success(client, fake_mp):
    rv = client.open_with_token(
        "/wechat-manager/login/start",
        method="POST",
        json={"fingerprint": FINGERPRINT},
    )
    assert rv.status_code == 200
    assert rv.json.get("expires_in") == 300
    assert rv.json.get("qrcode") == fake_mp["qrcode"]
    login_id = rv.json.get("login_id")
    assert login_id
    assert db_get_login(login_id) is not None


def test_login_start_rejected(client, fake_mp):
    fake_mp["startlogin_ret"] = 200004
    rv = client.open_with_token(
        "/wechat-manager/login/start",
        method="POST",
        json={"fingerprint": FINGERPRINT},
    )
    assert rv.status_code == 502
    assert rv.json.get("errid") == "MpLoginStartRejected"
    assert "200004" in rv.json.get("message")


def test_login_poll_no_state(client):
    rv = client.open_with_token("/wechat-manager/login/doesnotexist")
    assert rv.status_code == 404
    assert rv.json.get("errid") == "MpLoginNoState"


def test_login_poll_scanned(client, fake_mp):
    login_row = WechatLoginSession.create(
        fingerprint=FINGERPRINT, sessionid="123", user_agent="ua"
    )
    fake_mp["ask"] = {"base_resp": {"ret": 0}, "status": 4, "acct_size": 1}
    rv = client.open_with_token(f"/wechat-manager/login/{login_row.id}")
    assert rv.status_code == 200
    assert rv.json.get("state") == "scanned"
    assert rv.json.get("acct_size") == 1


def test_login_poll_need_email(client, fake_mp):
    login_row = WechatLoginSession.create(
        fingerprint=FINGERPRINT, sessionid="123", user_agent="ua"
    )
    fake_mp["ask"] = {"base_resp": {"ret": 0}, "status": 5}
    rv = client.open_with_token(f"/wechat-manager/login/{login_row.id}")
    assert rv.status_code == 200
    assert rv.json.get("state") == "need_email"


def test_login_poll_qrcode_refreshed(client, fake_mp):
    login_row = WechatLoginSession.create(
        fingerprint=FINGERPRINT, sessionid="123", user_agent="ua"
    )
    fake_mp["ask"] = {"base_resp": {"ret": 0}, "status": 2}
    rv = client.open_with_token(f"/wechat-manager/login/{login_row.id}")
    assert rv.status_code == 200
    assert rv.json.get("state") == "pending"
    assert rv.json.get("qrcode") == fake_mp["qrcode"]
    assert db_get_login(login_row.id) is not None


def test_login_poll_done(client, fake_mp):
    login_row = WechatLoginSession.create(
        fingerprint=FINGERPRINT, sessionid="123", user_agent="ua"
    )
    fake_mp["ask"] = {"base_resp": {"ret": 0}, "status": 1}
    rv = client.open_with_token(f"/wechat-manager/login/{login_row.id}")
    assert rv.status_code == 200
    assert rv.json.get("state") == "done"
    assert db_get_login(login_row.id) is None
    session_row = WechatSession.get_active()
    assert session_row is not None
    assert session_row.token == "1234567890"
    assert session_row.fingerprint == FINGERPRINT


@pytest.mark.usefixtures("fake_mp")
def test_session_status(client):
    rv = client.open_with_token("/wechat-manager/session")
    assert rv.status_code == 200
    assert rv.json.get("logged_in") is False

    WechatSession.store(
        cookies="[]", fingerprint=FINGERPRINT, token="123", user_agent="ua"
    )
    rv = client.open_with_token("/wechat-manager/session")
    assert rv.status_code == 200
    assert rv.json.get("logged_in") is True


@pytest.mark.usefixtures("fake_mp")
def test_session_check(client):
    rv = client.open_with_token("/wechat-manager/session/check", method="POST")
    assert rv.status_code == 200
    assert rv.json.get("valid") is False

    WechatSession.store(
        cookies="[]", fingerprint=FINGERPRINT, token="123", user_agent="ua"
    )
    rv = client.open_with_token("/wechat-manager/session/check", method="POST")
    assert rv.status_code == 200
    assert rv.json.get("valid") is True
    assert WechatSession.get_active().last_check_at is not None


def test_session_check_upstream_error(client, fake_mp):
    WechatSession.store(
        cookies="[]", fingerprint=FINGERPRINT, token="123", user_agent="ua"
    )
    fake_mp["check_home"] = None
    rv = client.open_with_token("/wechat-manager/session/check", method="POST")
    assert rv.status_code == 502


@pytest.mark.usefixtures("client")
def test_fetch_avatar_without_session():
    assert core.fetch_avatar("oX") is None


@pytest.mark.usefixtures("client", "fake_mp")
def test_fetch_avatar():
    WechatSession.store(
        cookies="[]", fingerprint=FINGERPRINT, token="123", user_agent="ua"
    )
    url = core.fetch_avatar("oX")
    assert url == HEAD_IMG_URL.replace("/64", "/0")


@pytest.mark.usefixtures("client")
def test_fetch_avatar_no_fans_info(fake_mp):
    WechatSession.store(
        cookies="[]", fingerprint=FINGERPRINT, token="123", user_agent="ua"
    )
    fake_mp["head_img_url"] = None
    assert core.fetch_avatar("oX") is None
