import json
import os

import click
from flask.cli import with_appcontext

from pkuphysu_wechat.wechat import wechat_client

os.environ["FLASK_APP"] = "pkuphysu_wechat"


@click.group()
def cli():
    "Managing wechat."
    pass


@cli.command("menu")
@with_appcontext
def menu():
    "Update menu"
    menu_file = os.path.join(os.path.dirname(__file__), "menu.json")
    with open(menu_file, "r", encoding="utf8") as f:
        menu_data = json.load(f)
    print(menu_data)
    wechat_client.create_menu(menu_data)


@cli.command("get_menu")
@with_appcontext
def get_menu():
    print(wechat_client.get_menu())
