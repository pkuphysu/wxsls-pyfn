from flask import Flask
from flask_jwt_extended.jwt_manager import JWTManager
from flask_sqlalchemy import SQLAlchemy

from .config import settings
from .utils import CustomBaseQuery, respond_error

db = SQLAlchemy(query_class=CustomBaseQuery)


def create_app():
    app = Flask(__name__)
    app.config.update(settings.flask)

    JWTManager(app)
    db.init_app(app)

    from . import auth, tasks, wechat

    app.register_blueprint(wechat.bp)
    app.register_blueprint(tasks.bp)
    app.register_blueprint(auth.bp)

    app.errorhandler(500)(lambda e: respond_error(500, "UnkownError", e.description))

    return app
