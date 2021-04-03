from flask import Flask
from flask_jwt_extended.jwt_manager import JWTManager
from flask_sqlalchemy import SQLAlchemy

from .config import settings

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.update(settings.flask)

    JWTManager(app)
    db.init_app(app)

    from . import tasks, wechat

    app.register_blueprint(wechat.bp)
    app.register_blueprint(tasks.bp)

    db.create_all(app=app)

    return app
