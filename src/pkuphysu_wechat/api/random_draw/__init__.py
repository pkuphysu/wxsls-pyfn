from flask import Blueprint

bp = Blueprint("random_draw", __name__, url_prefix="/api/random-draw")

from . import routes  # noqa
