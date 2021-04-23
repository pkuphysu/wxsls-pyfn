from logging import getLogger

from flask import abort, request

from pkuphysu_wechat.config import settings
from pkuphysu_wechat.utils import respond_error

from .models import UserToken

__all__ = ["token_required", "master_required"]
logger = getLogger(__name__)


def token_required() -> str:
    """Get the openid of current user in token protected views. Abort if bad token.

    :return: openid
    :rtype: str
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        abort(respond_error(401, "TokenRequired"))
    token = auth_header.replace("Basic ", "", 1)
    if not settings.PRODUCTION and token == "developmentoken":
        return "developmentopenid"
    token_record = UserToken.query.get(token)
    if not token_record or token_record.expired(settings.TOKEN_EXPIRY):
        abort(respond_error(401, "BadToken"))
    return token_record.openid


def master_required():
    openid = token_required()
    if openid not in settings.WECHAT.MASTER_IDS:
        logger.info("%s tried to access admin resouces", openid)
        abort(respond_error(403, "NoHackMaster"))


def master_before_request():
    if request.method != "OPTIONS":
        master_required()
