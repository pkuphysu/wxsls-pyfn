from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from .config import settings
from .utils import CustomBaseQuery, respond_error

db = SQLAlchemy(query_class=CustomBaseQuery)


def create_app():
    app = Flask(__name__)
    app.config.update(settings.flask)

    db.init_app(app)

    if not settings.PRODUCTION:
        from flask_cors import CORS

        print(settings.PRODUCTION)
        CORS(app, origins="http://localhost:3000")

    from . import api, auth, dba, tasks, wechat

    api.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(dba.bp)
    app.register_blueprint(tasks.bp)
    app.register_blueprint(wechat.bp)

    app.errorhandler(500)(lambda e: respond_error(500, "UnkownError", e.description))

    return app
