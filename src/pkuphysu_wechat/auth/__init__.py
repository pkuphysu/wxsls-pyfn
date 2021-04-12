from flask import Blueprint

bp = Blueprint("auth", __name__, url_prefix="/auth")


from . import routes  # NOQA
from .utils import token_required  # NOQA
