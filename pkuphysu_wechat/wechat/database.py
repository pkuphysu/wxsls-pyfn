# from base64 import b64encode
import json
import urllib.request
from datetime import datetime, timedelta
from logging import getLogger
from typing import Dict

from pkuphysu_wechat import db
from pkuphysu_wechat.config import settings

URL = (
    "https://api.weixin.qq.com/cgi-bin/token"
    "?grant_type=client_credential&appid={}&secret={}"
).format(settings.wechat.APP_ID, settings.wechat.APP_SECRET)
logger = getLogger(__name__)


class AccessToken(db.Model):
    """
    Table to store wechat access_token and its expire time for global use

    The official expire time is 7200s, but it's better to fetch a new one
        slightly earlier, so we will set it to 7000s
    """

    __tablename__ = "access_token"

    token = db.Column(db.String(512), primary_key=True)
    expire_time = db.Column(db.DateTime())

    @classmethod
    def get(cls) -> str:
        access_token = cls.query.first()
        now = datetime.now()
        if access_token is not None:
            if access_token.expire_time > now:
                return access_token.token
            db.session.delete(access_token)

        response = urllib.request.urlopen(URL)
        js_str = response.read().decode()
        js = json.loads(js_str)
        logger.debug(js)
        token = js["access_token"]
        expire_time = now + timedelta(seconds=7000)
        db.session.add(cls(token=token, expire_time=expire_time))
        db.session.commit()
        return token


class CommandStatus(db.Model):
    __tablename__ = "command_status"

    name = db.Column(db.String(32), primary_key=True)
    status = db.Column(db.Boolean, nullable=False)

    @classmethod
    def set_status(cls, name: str, status: bool) -> None:
        db.session.merge(cls(name=name, status=status))
        db.session.commit()

    @classmethod
    def get_all_status(cls) -> Dict[str, bool]:
        return {c.name: c.status for c in cls.query.all()}


class AutoReply(db.Model):
    __table_name__ = "auto_reply"

    keyword = db.Column(db.Unicode(32), primary_key=True)
    response = db.Column(db.String(2048))

    @classmethod
    def update(cls, keyword, response):
        db.session.merge(cls(keyword=keyword, response=response))
        db.session.commit()

    @classmethod
    def remove(cls, keyword):
        rows = cls.query.filter(cls.keyword == keyword).delete()
        db.session.commit()
        return rows
