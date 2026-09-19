import json
from base64 import b64encode
from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import getLogger

from pkuphysu_wechat import db
from pkuphysu_wechat.config import settings
from pkuphysu_wechat.wechat_manager import fetch_avatar, get_mp_credentials

logger = getLogger(__name__)


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


def avatar_data_uri(avatar: bytes):
    "头像字节来自 wx.qlogo.cn 快照，恒为 jpeg"
    if not avatar:
        return None
    return "data:image/jpeg;base64," + b64encode(avatar).decode("ascii")


class CJParticipant(db.Model):
    __tablename__ = "CJParticipant"

    event = db.Column(db.String(32), default=settings.eveparty.EVENT, primary_key=True)
    open_id = db.Column(db.String(32), primary_key=True)
    name = db.Column(db.String(16), nullable=False)
    stu_id = db.Column(db.String(32), nullable=False)
    investment = db.Column(db.String(32), nullable=False)
    avatar_url = db.Column(db.String(256))
    avatar = db.Column(db.LargeBinary)

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
        user.investment = json.dumps(investment)
        db.session.add(user)
        db.session.commit()

    @classmethod
    @get_user
    def get_user_name(cls, user):
        return user.name

    @classmethod
    def update_avatar(cls, open_id) -> bool:
        "Fetch one avatar via wechat_manager; no-op when no backend session exists"
        fetched = fetch_avatar(open_id)
        if not fetched:
            return False
        user = db.session.get(
            cls, {"event": settings.eveparty.EVENT, "open_id": open_id}
        )
        if user is None:
            return False
        user.avatar_url, user.avatar = fetched
        db.session.commit()
        return True

    @classmethod
    def refresh_avatars(cls) -> dict:
        "Batch refresh avatars for all participants of the current event"
        users = cls.query.filter(cls.event == settings.eveparty.EVENT).all()
        credentials = get_mp_credentials()
        if credentials is None:
            logger.info("CJAvatarRefreshSkipped: no mp backend session")
            return {"total": len(users), "updated": 0, "failed": len(users)}
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = {
                # 线程里不碰 DB，会话以主线程取出的快照传入
                pool.submit(fetch_avatar, user.open_id, credentials): user.open_id
                for user in users
            }
            fetched = {}
            for future in as_completed(futures):
                open_id = futures[future]
                try:
                    fetched[open_id] = future.result()
                except Exception:
                    logger.exception("CJAvatarFetchCrashed openid=%s", open_id)
                    fetched[open_id] = None
        updated = 0
        for user in users:
            result = fetched.get(user.open_id)
            if not result:
                continue
            user.avatar_url, user.avatar = result
            updated += 1
        db.session.commit()
        return {"total": len(users), "updated": updated, "failed": len(users) - updated}

    @classmethod
    def to_cj_json(cls):
        return {
            user.name: {
                "investment": json.loads(user.investment),
                "avatar_url": user.avatar_url,
                "avatar": avatar_data_uri(user.avatar),
            }
            for user in cls.query.filter(cls.event == settings.eveparty.EVENT).all()
        }
