import os
from dotenv import load_dotenv
from flask import Flask, redirect, url_for

from app.extensions import db
from app.auth import auth_bp, current_user
from app.oauth import oauth_bp

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ["FLASK_SECRET_KEY"]
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URI"]
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SESSION_COOKIE_NAME"] = "auth_session"

    db.init_app(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(oauth_bp)

    with app.app_context():
        db.create_all()

    @app.route("/")
    def index():
        u = current_user()
        if u:
            return f"<h3>Hello {u.email}</h3><a href='/logout'>Logout</a>"
        return redirect(url_for("auth.login"))

    return app