from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from .config import settings
from .utils import CustomBaseQuery, respond_error

db = SQLAlchemy(query_class=CustomBaseQuery)


def create_app():
    app = Flask(__name__)
    app.config.update(settings.flask)

    db.init_app(app)

    from . import api, auth, tasks, wechat

    api.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(tasks.bp)
    app.register_blueprint(wechat.bp)

    app.errorhandler(500)(lambda e: respond_error(500, "UnkownError", e.description))

    return app
