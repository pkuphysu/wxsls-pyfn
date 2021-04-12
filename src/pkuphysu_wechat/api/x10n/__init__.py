from logging import getLogger

from flask import Blueprint, jsonify, request

from pkuphysu_wechat.auth import token_required

from .database import Datax10n

logger = getLogger(__name__)
bp = Blueprint("x10n", __name__)


@bp.route("/api/x10n", methods=["GET", "POST"])
def index():
    openid = token_required()
    if request.method == "GET":
        return jsonify(Datax10n.get_info(openid))
    # if request.method == 'DELETE':
    #     Datax10n.del_info(raw_id)
    if Datax10n.put_info(openid, request.data.decode()):
        return {"msg": "success"}
    return {"msg": "da lao rao ming"}
