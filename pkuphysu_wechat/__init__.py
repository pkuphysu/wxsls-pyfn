from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy

from .config import settings

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.update(settings.flask)

    db.init_app(app)

    from . import tasks, wechat

    app.register_blueprint(wechat.bp)
    app.register_blueprint(tasks.bp)

    db.create_all(app=app)

    @app.route("/echo", methods=["POST", "GET"])
    def echo():
        response = request.args.get("q")
        if not response:
            print(request.form)
            response = request.form.get("q", "NA")
        return response

    return app
