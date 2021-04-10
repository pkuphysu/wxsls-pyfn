from flask import abort, request

from pkuphysu_wechat.config import settings
from pkuphysu_wechat.utils import respond_error

from .database import UserToken

__all__ = ["token_required"]


def token_required() -> str:
    """Get the openid of current user in token protected views. Abort if bad token.

    :return: openid
    :rtype: str
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        abort(respond_error(401, "TokenRequired"))
    token = auth_header.replace("Basic ", "", 1)
    token_record = UserToken.query.get(token)
    if not token_record or token_record.expired(settings.TOKEN_EXPIRY):
        abort(respond_error(401, "BadToken"))
    return token_record.openid