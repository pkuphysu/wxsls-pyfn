import json

from pkuphysu_wechat import db
from pkuphysu_wechat.config import settings


def get_user(f):
    def func(cls, open_id, *args, **kargs):
        user = cls.query.get({"event": settings.eveparty.EVENT, "open_id": open_id})
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
    def to_cj_json(cls):
        return {
            user.name: json.loads(user.investment)
            for user in cls.query.filter(cls.event == settings.eveparty.EVENT).all()
        }
