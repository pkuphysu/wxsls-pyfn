from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import HTTPException

from .config import settings
from .utils import CustomBaseQuery, respond_error

db = SQLAlchemy(query_class=CustomBaseQuery)


def create_app():
    app = Flask(__name__)
    app.config.update(settings.flask)

    db.init_app(app)

    if not settings.PRODUCTION:
        from flask_cors import CORS

        CORS(app, origins="http://localhost:3000")

    from . import api, auth, dba, tasks, wechat

    api.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(dba.bp)
    app.register_blueprint(tasks.bp)
    app.register_blueprint(wechat.bp)

    app.register_error_handler(
        HTTPException, lambda e: respond_error(e.code, "GeneralError", e.description)
    )
    return app
