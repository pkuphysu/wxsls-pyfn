import functools
import os.path
from typing import Callable

from flask import Blueprint, abort, request

from pkuphysu_wechat.config import settings
from pkuphysu_wechat.wechat import wechat_client

bp = Blueprint("tasks", __name__, url_prefix="/tasks")


def auth_required(func: Callable):
    @functools.wraps(func)
    def f(*args, **kwargs):
        if request.args.get("token", "") != settings.TASK_AUTH_TOKEN:
            abort(401)
        return func(*args, **kwargs)

    return f


@bp.route("/menu")
@auth_required
def menu():
    "Update menu"
    menu_file = os.path.join(os.path.dirname(__file__), "menu.json")
    with open(menu_file, "rb") as f:
        menu_data = f.read()
    wechat_client.create_menu(menu_data)
    return "Menu Updated"
