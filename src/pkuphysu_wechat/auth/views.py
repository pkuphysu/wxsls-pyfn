from logging import getLogger

from flask import Blueprint, request
from werobot.client import ClientException

from pkuphysu_wechat.config import settings
from pkuphysu_wechat.utils import respond_error, respond_success
from pkuphysu_wechat.wechat import wechat_client

from .models import TokenCode, UserToken
from .utils import token_required

logger = getLogger(__name__)

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/wechat")
def auth():
    code = request.args.get("code")
    if not code:
        return respond_error(400, "AuthNoCode")
    try:
        oauth_response = wechat_client.oauth(code)
    except ClientException as e:
        logger.info("Bad auth code %s: %s", code, e.args[0])
        return respond_error(400, "AuthBadCode", e.args[0])
    openid = oauth_response.get("openid")
    if not openid:
        logger.error(
            "Cannot find openid in %s, even no error given", str(oauth_response)
        )
        return respond_error(503, "AuthTencentSucks")
    return respond_success(token=UserToken.create(openid))


# `tcode` is short for token_code
@bp.route("/tcode/get")
def get_tcode():
    return respond_success(tcode=TokenCode.create())


@bp.route("/tcode/grant")
def grant_tcode():
    openid = token_required()
    tcode_record = TokenCode.query.get_or_abort(
        request.args.get("tcode"), 400, "AuthNoTCode", "AuthBadTCode"
    )
    if tcode_record.expired(settings.TCODE_EXPIRY):
        return respond_error(400, "AuthBadTCode")
    new_token = UserToken.create(openid)
    tcode_record.bind_token(new_token)
    return respond_success()


@bp.route("/tcode/exchange")
def exchange_token():
    tcode_record = TokenCode.query.get_or_abort(
        request.args.get("tcode"), 400, "ExchangeNoTCode", "ExchangeBadTCode"
    )
    if tcode_record.expired(settings.TCODE_EXPIRY):
        return respond_error(400, "ExchangeBadTCode")
    token = tcode_record.get_token()
    if not token:
        return respond_error(404, "ExchangeNoToken")
    return respond_success(token=token)


@bp.route("/openid")
def get_openid():
    return respond_success(openid=token_required())
