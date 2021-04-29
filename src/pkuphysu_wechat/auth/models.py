import datetime
import os
from base64 import urlsafe_b64encode

from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.sql import func

from pkuphysu_wechat import db


def expired_and_handle(record, expiry: int) -> bool:
    """Handle record expiry

    :param record: database ORM record
    :type record: Any
    :param expiry: Expiry time in seconds
    :type expiry: int
    :return: Expired or not
    :rtype: bool
    """
    expired = (
        record.created_at + datetime.timedelta(seconds=expiry) < datetime.datetime.now()
    )
    if expired:
        db.session.delete(record)
        db.session.commit()
    return expired


class User(db.Model):
    __tablename__ = "user"
    openid = db.Column(db.String(32), primary_key=True)
    nickname = db.Column(db.String(32))
    avatar = db.Column(BYTEA())

    def update(self):
        db.session.merge(self)
        db.session.commit()


class UserToken(db.Model):
    __tablename__ = "user_token"
    token = db.Column(db.String(32), primary_key=True)
    openid = db.Column(db.String(32))
    created_at = db.Column(db.DateTime, server_default=func.now())

    @classmethod
    def create(cls, openid: str = None) -> str:
        """Create a new user token

        :param openid: openid of the user the token belongs to.
            None means blank token waiting for auth. defaults to None
        :type openid: str, optional
        :return: The created token
        :rtype: str
        """
        token = urlsafe_b64encode(os.urandom(24)).decode("ascii")
        db.session.add(cls(token=token, openid=openid))
        db.session.commit()
        return token

    def expired(self, expiry: int) -> bool:
        return expired_and_handle(self, expiry)


class TokenCode(db.Model):
    "A temporary code to get real user token"
    __tablename__ = "token_code"
    code = db.Column(db.String(16), primary_key=True)
    token = db.Column(db.String(32))
    created_at = db.Column(db.DateTime, server_default=func.now())

    @classmethod
    def create(cls):
        code = urlsafe_b64encode(os.urandom(12)).decode("ascii")
        db.session.add(cls(code=code))
        db.session.commit()
        return code

    def bind_token(self, token: str):
        self.token = token
        db.session.commit()

    def get_token(self):
        token = self.token
        db.session.delete(self)
        db.session.commit()
        return token

    def expired(self, expiry: int) -> bool:
        return expired_and_handle(self, expiry)
