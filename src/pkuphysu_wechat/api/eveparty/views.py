from flask import Blueprint, abort

from pkuphysu_wechat.auth import token_required
from pkuphysu_wechat.config import settings
from pkuphysu_wechat.utils import respond_success

from .models import CJParticipant

bp = Blueprint("eveparty", __name__)


@bp.route("/api/choujiang", methods=["GET"])
def cj_data():
    openid = token_required()
    if openid not in settings.wechat.MASTER_IDS:
        abort(404)
    return respond_success(data=CJParticipant.to_cj_json())
