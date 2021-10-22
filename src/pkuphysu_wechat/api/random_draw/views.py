from flask import Blueprint, abort, request

from pkuphysu_wechat.auth import token_required
from pkuphysu_wechat.config import settings
from pkuphysu_wechat.utils import respond_error, respond_success

from .models import RandomDraw

bp = Blueprint("random_draw", __name__, url_prefix="/api/random-draw")


@bp.route("/join", methods=["POST"])
def join():
    openid = token_required()
    name = request.json.get("name")
    if not name:
        return respond_error(400, "DrawNameRequired")
    if RandomDraw.add_participant(openid, name):
        return respond_success()
    else:
        return respond_error(400, "DrawNotAgain")


@bp.route("/all", methods=["GET"])
def get_all():
    openid = token_required()
    if openid not in settings.WECHAT.MASTER_IDS and not (
        openid == "developmentopenid" and not settings.PRODUCTION
    ):
        abort(404)
    return respond_success(data=[record.name for record in RandomDraw.query.all()])
