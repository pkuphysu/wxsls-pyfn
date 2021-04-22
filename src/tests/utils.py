from dataclasses import dataclass

from flask.testing import FlaskClient
from werkzeug.datastructures import Headers

from pkuphysu_wechat import settings
from pkuphysu_wechat.wechat import wechat_mgr


@dataclass
class FakeTextMessage:
    content: str
    source: str


def mock_exec(content, master=False):
    source = settings.wechat.MASTER_IDS[0] if master else ""
    return wechat_mgr.exec(
        content, message=FakeTextMessage(content=content, source=source)
    )


class Client(FlaskClient):
    def open_with_token(self, *args, **kwargs):
        headers = kwargs.pop("headers", Headers())
        headers.extend(Headers({"Authorization": "Basic developmentoken"}))
        kwargs["headers"] = headers
        return super().open(*args, **kwargs)
