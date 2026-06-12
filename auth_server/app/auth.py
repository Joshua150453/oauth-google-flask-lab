from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.extensions import db
from app.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        if User.query.filter_by(email=email).first():
            flash("Email already registered", "error")
            return redirect(url_for("auth.register"))
        user = User(email=email, name=request.form.get("name", ""))
        user.set_password(request.form["password"])
        db.session.add(user)
        db.session.commit()
        session["uid"] = user.id
        return redirect(request.args.get("next", "/"))
    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"].strip().lower()).first()
        if user and user.check_password(request.form["password"]):
            session["uid"] = user.id
            return redirect(request.args.get("next", "/"))
        flash("Invalid credentials", "error")
    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


def current_user():
    uid = session.get("uid")
    return db.session.get(User, uid) if uid else None