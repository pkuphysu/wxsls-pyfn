from datetime import datetime, timedelta
from logging import getLogger
from typing import Callable, Dict

from pkuphysu_wechat import db

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
    def get(cls, token_getter: Callable) -> str:
        access_token = cls.query.first()
        now = datetime.now()
        if access_token is not None:
            if access_token.expire_time > now:
                return access_token.token
            db.session.delete(access_token)

        json_response = token_getter()
        if "access_token" not in json_response:
            raise ValueError("Access token not found in " + json_response)
        token = json_response["access_token"]
        expire_time = now + timedelta(seconds=json_response["expires_in"])
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
