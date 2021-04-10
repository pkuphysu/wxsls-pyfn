from logging import getLogger

from flask import request

from pkuphysu_wechat.auth.database import TokenCode, UserToken
from pkuphysu_wechat.config import settings
from pkuphysu_wechat.utils import respond_error, respond_success
from pkuphysu_wechat.wechat import wechat_client

from . import bp
from .utils import token_required

logger = getLogger()


@bp.route("/wechat")
def auth():
    code = request.args.get("code")
    if not code:
        return respond_error(400, "AuthNoCode")
    oauth_response = wechat_client.oauth(code)
    oauth_errmsg = oauth_response.get("errmsg")
    if oauth_errmsg:
        logger.info("Bad auth code %s: %s", code, oauth_errmsg)
        return respond_error(400, "AuthBadCode", oauth_errmsg)
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
