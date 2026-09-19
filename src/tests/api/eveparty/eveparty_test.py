from types import SimpleNamespace

import pytest

from pkuphysu_wechat import settings
from pkuphysu_wechat.api.eveparty.models import CJParticipant
from pkuphysu_wechat.wechat import wechat_mgr

IMAGE_BYTES = b"\xff\xd8fakejpeg"
AVATAR_URL = "https://wx.qlogo.cn/mmopen/xyz/0"


@pytest.fixture()
def fake_fetch(monkeypatch):
    calls = []

    def fetch(openid, _credentials=None):
        calls.append(openid)
        return AVATAR_URL, IMAGE_BYTES

    monkeypatch.setattr("pkuphysu_wechat.api.eveparty.models.fetch_avatar", fetch)
    return calls


@pytest.fixture()
def fake_credentials(monkeypatch):
    monkeypatch.setattr(
        "pkuphysu_wechat.api.eveparty.models.get_mp_credentials",
        lambda: ("[]", "f" * 32, "123", "ua"),
    )


@pytest.fixture()
def participant(client):  # pylint: disable=unused-argument
    "client is requested for its app context and class-scope ordering"
    CJParticipant.add_user("oAlice", "小明", "2100000000")
    return CJParticipant.query.filter_by(open_id="oAlice").first()


@pytest.mark.usefixtures("participant")
def test_choujiang_shape(client):
    rv = client.open_with_token("/api/choujiang")
    assert rv.status_code == 200
    entry = rv.json["data"]["小明"]
    assert entry["investment"] == [1, 1, 1]
    assert entry["avatar_url"] is None
    assert entry["avatar"] is None


@pytest.mark.usefixtures("participant")
def test_choujiang_requires_master(client, monkeypatch):
    from pkuphysu_wechat.auth.models import UserToken

    monkeypatch.setitem(settings["WECHAT"], "MASTER_IDS", [])
    token = UserToken.create("oEvil")
    rv = client.get("/api/choujiang", headers=[("Authorization", f"Basic {token}")])
    assert rv.status_code == 403
    assert rv.json.get("errid") == "NoHackMaster"
    rv = client.post(
        "/api/choujiang/avatars/refresh",
        headers=[("Authorization", f"Basic {token}")],
    )
    assert rv.status_code == 403


@pytest.mark.usefixtures("client", "participant")
def test_update_avatar(fake_fetch):
    assert CJParticipant.update_avatar("oAlice") is True
    user = CJParticipant.query.filter_by(open_id="oAlice").first()
    assert user.avatar_url == AVATAR_URL
    assert user.avatar == IMAGE_BYTES
    assert fake_fetch == ["oAlice"]


@pytest.mark.usefixtures("client", "participant")
def test_update_avatar_without_session(monkeypatch):
    monkeypatch.setattr(
        "pkuphysu_wechat.api.eveparty.models.fetch_avatar", lambda openid: None
    )
    assert CJParticipant.update_avatar("oAlice") is False
    user = CJParticipant.query.filter_by(open_id="oAlice").first()
    assert user.avatar_url is None
    assert user.avatar is None


def test_invest_triggers_avatar_fetch(client, fake_fetch):
    wechat_mgr.command_reg.set_status("eveparty", True)
    CJParticipant.add_user("oBob", "小红", "2100000001")
    reply = wechat_mgr.exec(
        "invest 10 20 30",
        message=SimpleNamespace(content="invest 10 20 30", source="oBob"),
    )
    assert "投点成功" in reply
    assert fake_fetch == ["oBob"]
    user = CJParticipant.query.filter_by(open_id="oBob").first()
    assert user.avatar == IMAGE_BYTES
    rv = client.open_with_token("/api/choujiang")
    entry = rv.json["data"]["小红"]
    assert entry["investment"] == [10, 20, 30]
    assert entry["avatar_url"] == AVATAR_URL
    assert entry["avatar"].startswith("data:image/jpeg;base64,")


@pytest.mark.usefixtures("client", "participant", "fake_credentials")
def test_refresh_avatars(monkeypatch):
    CJParticipant.add_user("oNobody", "小刚", "2100000002")

    def fetch_one(openid, credentials=None):
        assert credentials == ("[]", "f" * 32, "123", "ua")
        if openid == "oNobody":
            return None
        return AVATAR_URL, IMAGE_BYTES

    monkeypatch.setattr("pkuphysu_wechat.api.eveparty.models.fetch_avatar", fetch_one)
    assert CJParticipant.refresh_avatars() == {
        "total": 2,
        "updated": 1,
        "failed": 1,
    }
    user = CJParticipant.query.filter_by(open_id="oAlice").first()
    assert user.avatar == IMAGE_BYTES
    nobody = CJParticipant.query.filter_by(open_id="oNobody").first()
    assert nobody.avatar is None


@pytest.mark.usefixtures("client", "participant")
def test_refresh_avatars_without_session(fake_fetch, monkeypatch):
    monkeypatch.setattr(
        "pkuphysu_wechat.api.eveparty.models.get_mp_credentials", lambda: None
    )
    assert CJParticipant.refresh_avatars() == {
        "total": 1,
        "updated": 0,
        "failed": 1,
    }
    assert fake_fetch == []


@pytest.mark.usefixtures("participant", "fake_fetch", "fake_credentials")
def test_refresh_avatars_view(client):
    rv = client.open_with_token("/api/choujiang/avatars/refresh", method="POST")
    assert rv.status_code == 200
    assert rv.json["data"] == {"total": 1, "updated": 1, "failed": 0}
