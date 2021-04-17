from flask import abort, request

from pkuphysu_wechat.auth.utils import token_required
from pkuphysu_wechat.config import settings
from pkuphysu_wechat.utils import respond_error, respond_success

from . import bp
from .database import RandomDraw


@bp.route("/join", methods=["POST"])
def join():
    openid = token_required()
    name = request.form.get("name")
    if not name:
        return respond_error(400, "DrawNameRequired")
    if RandomDraw.add_participant(openid, name):
        return respond_success()
    else:
        return respond_error(400, "DrawNotAgain")


@bp.route("/all", methods=["GET"])
def get_all():
    openid = token_required()
    if openid not in settings.wechat.MASTER_IDS:
        abort(404)
    return respond_success(data=[record.name for record in RandomDraw.query.all()])
