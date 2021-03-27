from dataclasses import dataclass

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
