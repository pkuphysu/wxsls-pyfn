from logging import getLogger

from flask import abort, request
from flask_jwt_extended import create_access_token

from pkuphysu_wechat.wechat import wechat_client

from . import bp

logger = getLogger()


@bp.route("/auth")
def auth():
    code = request.args.get("code")
    if code is None:
        abort(400)
    oauth_response = wechat_client.oauth(code)
    openid = oauth_response.get("openid")
    if openid is None:
        logger.error("Cannot find openid in %s", str(oauth_response))
    return {"token": create_access_token(identity=openid)}
