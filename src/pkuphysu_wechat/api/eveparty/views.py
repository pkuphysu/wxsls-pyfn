from flask import Blueprint

from pkuphysu_wechat.auth.utils import master_required
from pkuphysu_wechat.utils import respond_success

from .models import CJParticipant

bp = Blueprint("eveparty", __name__)


@bp.route("/api/choujiang", methods=["GET"])
def cj_data():
    master_required()
    return respond_success(data=CJParticipant.to_cj_json())


@bp.route("/api/choujiang/avatars/refresh", methods=["POST"])
def cj_refresh_avatars():
    master_required()
    return respond_success(data=CJParticipant.refresh_avatars())
