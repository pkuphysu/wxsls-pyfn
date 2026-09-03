import base64
import json
import logging

import requests
from werobot.client import ClientException

from pkuphysu_wechat import db
from pkuphysu_wechat.config import settings

logger = logging.getLogger(__name__)


def get_user(f):
    def func(cls, open_id, *args, **kargs):
        user = db.session.get(
            cls, {"event": settings.eveparty.EVENT, "open_id": open_id}
        )
        if user is None:
            return False
        resp = f(cls, user, *args, **kargs)
        if resp is not None:
            return resp
        return True

    return func


class CJParticipant(db.Model):
    __tablename__ = "CJParticipant"

    event = db.Column(db.String(32), default=settings.eveparty.EVENT, primary_key=True)
    open_id = db.Column(db.String(32), primary_key=True)
    name = db.Column(db.String(16), nullable=False)
    stu_id = db.Column(db.String(32), nullable=False)
    investment = db.Column(db.String(32), nullable=False)
    avatar = db.Column(db.LargeBinary(), nullable=True)

    @classmethod
    def add_user(cls, open_id, name, stu_id):
        db.session.merge(
            cls(
                open_id=open_id,
                name=name,
                stu_id=stu_id,
                investment=json.dumps([1] * settings.eveparty.PRIZE_COUNT),
            )
        )
        db.session.commit()

    @classmethod
    @get_user
    def user_invest(cls, user, investment):
        from pkuphysu_wechat.wechat import wechat_client

        user.investment = json.dumps(investment)
        try:
            user_info = wechat_client.get(
                url="https://api.weixin.qq.com/cgi-bin/user/info",
                params={
                    "access_token": wechat_client.get_access_token(),
                    "openid": user.open_id,
                    "lang": "zh_CN",
                },
            )
            avatar_url = user_info.get("headimgurl") if user_info else None
            if avatar_url:
                avatar_response = requests.get(avatar_url, timeout=10)
                avatar_response.raise_for_status()
                user.avatar = avatar_response.content
        except (
            ClientException,
            KeyError,
            requests.RequestException,
            ValueError,
        ) as error:
            logger.warning("Unable to update avatar for %s: %s", user.open_id, error)
        db.session.add(user)
        db.session.commit()

    @classmethod
    @get_user
    def get_user_name(cls, user):
        return user.name

    @classmethod
    def to_cj_json(cls):
        return {
            user.name: {
                "investment": json.loads(user.investment),
                "avatar": (
                    "data:image/jpeg;base64,"
                    + base64.b64encode(user.avatar).decode("ascii")
                    if user.avatar
                    else None
                ),
            }
            for user in cls.query.filter(cls.event == settings.eveparty.EVENT).all()
        }
