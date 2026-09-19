import os
from base64 import urlsafe_b64encode
from datetime import datetime, timedelta
from logging import getLogger

from sqlalchemy.sql import func

from pkuphysu_wechat import db

logger = getLogger(__name__)

LOGIN_TTL = 300


class WechatSession(db.Model):
    "Long-lived logged-in session of the mp.weixin.qq.com backend, one global row"

    __tablename__ = "wechat_session"

    id = db.Column(db.Integer, primary_key=True)
    mp_account = db.Column(db.String(64))
    fingerprint = db.Column(db.String(32), nullable=False)
    cookies = db.Column(db.Text, nullable=False)
    token = db.Column(db.String(32))
    user_agent = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())
    last_check_at = db.Column(db.DateTime)
    valid = db.Column(db.Boolean, default=True)

    @classmethod
    def store(cls, *, cookies, fingerprint, token, user_agent, mp_account=None):
        row = db.session.get(cls, 1)
        if row is None:
            row = cls(id=1)
            db.session.add(row)
        row.mp_account = mp_account or row.mp_account
        row.fingerprint = fingerprint
        row.cookies = cookies
        row.token = token
        row.user_agent = user_agent
        row.valid = True
        db.session.commit()

    @classmethod
    def get_active(cls):
        row = db.session.get(cls, 1)
        if row is not None and row.valid and row.token:
            return row
        return None

    @classmethod
    def mark_check(cls, valid: bool):
        row = db.session.get(cls, 1)
        if row is None:
            return
        row.last_check_at = datetime.now()
        row.valid = valid
        db.session.commit()


class WechatLoginSession(db.Model):
    "Short-lived state of a QR-code login in progress"

    __tablename__ = "wechat_login_session"

    id = db.Column(db.String(32), primary_key=True)
    fingerprint = db.Column(db.String(32), nullable=False)
    sessionid = db.Column(db.String(24), nullable=False)
    cookies = db.Column(db.Text)
    user_agent = db.Column(db.String(256), nullable=False)
    state = db.Column(db.String(16))
    created_at = db.Column(db.DateTime, server_default=func.now())

    @classmethod
    def create(cls, fingerprint, sessionid, user_agent):
        row = cls(
            id=urlsafe_b64encode(os.urandom(24)).decode("ascii"),
            fingerprint=fingerprint,
            sessionid=sessionid,
            user_agent=user_agent,
            state="started",
            # Python 侧赋值而非 server_default：expired() 与本地时钟比较，
            # 混用 DB 时钟会在时区不一致时立刻误判过期
            created_at=datetime.now(),
        )
        db.session.add(row)
        db.session.commit()
        return row

    def expired(self) -> bool:
        return self.created_at + timedelta(seconds=LOGIN_TTL) < datetime.now()

    def save(self):
        db.session.add(self)
        db.session.commit()
