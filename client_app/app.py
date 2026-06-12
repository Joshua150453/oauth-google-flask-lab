import os
import secrets
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv
from flask import Flask, redirect, request, session, render_template, url_for

load_dotenv()

print("FLASK_SECRET_KEY =", os.getenv("FLASK_SECRET_KEY"))

app = Flask(__name__)
app.config["SERVER_NAME"] = "localhost:5000"
app.secret_key = os.getenv("FLASK_SECRET_KEY")

app.config["SESSION_COOKIE_NAME"] = "client_session"
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False

CLIENT_ID     = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
AUTHORIZE_URL = os.environ["AUTHORIZE_URL"]
TOKEN_URL     = os.environ["TOKEN_URL"]
USERINFO_URL  = os.environ["USERINFO_URL"]
RES_URL       = os.environ["RESOURCE_SERVER_URL"]
REDIRECT_URI  = os.environ["REDIRECT_URI"]
SCOPE         = os.environ["SCOPE"]


@app.route("/")
def index():
    return render_template("index.html",
                           logged_in="access_token" in session)


@app.route("/login")
def login():
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state

    print("LOGIN STATE:", state)
    print("SESSION LOGIN:", dict(session))
    print("SESSION COOKIE NAME:", app.config.get("SESSION_COOKIE_NAME"))
    print("SECRET KEY:", app.secret_key)

    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
        "state": state,
    }
    print("SESSION BEFORE REDIRECT:", dict(session))
    return redirect(f"{AUTHORIZE_URL}?{urlencode(params)}")


@app.route("/oauth/callback")
def callback():
    print("FULL URL:", request.url)
    print("HOST:", request.host)
    print("COOKIES:", request.cookies)
    print("CALLBACK STATE:", request.args.get("state"))
    print("SESSION CALLBACK:", dict(session))

    if request.args.get("state") != session.pop("oauth_state", None):
        return "Invalid state (CSRF)", 400

    # Back-channel exchange
    token_resp = requests.post( TOKEN_URL, data={
        "grant_type":    "authorization_code",
        "code":          request.args["code"],
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri":  REDIRECT_URI,
    }, timeout=10)
    token_resp.raise_for_status()
    tokens = token_resp.json()
    print(tokens)
    userinfo = requests.get(
    USERINFO_URL,
    headers={
        "Authorization": f"Bearer {tokens['access_token']}"
    }
    ).json()

    print(userinfo)

    session["access_token"] = tokens["id_token"]
    return redirect(url_for("dashboard"))


def _api(method, path, **kwargs):
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    return requests.request(method, f"{RES_URL}{path}",
                            headers=headers, timeout=5, **kwargs)


@app.route("/dashboard")
def dashboard():
    if "access_token" not in session:
        return redirect(url_for("login"))

    me_resp = _api("GET", "/api/me")
    notes_resp = _api("GET", "/api/notes")

    if me_resp.status_code != 200:
        return f"API ERROR: {me_resp.text}"

    if notes_resp.status_code != 200:
        return f"API ERROR: {notes_resp.text}"

    me = me_resp.json()
    notes = notes_resp.json()

    return render_template("dashboard.html", me=me, notes=notes)


@app.route("/notes", methods=["POST"])
def create_note():
    if "access_token" not in session:
        return redirect(url_for("login"))

    _api("POST", "/api/notes", json={
        "title": request.form["title"],
        "body":  request.form.get("body", ""),
    })
    return redirect(url_for("dashboard"))


@app.route("/notes/<int:nid>/delete", methods=["POST"])
def delete_note(nid):
    if "access_token" not in session:
        return redirect(url_for("login"))
    _api("DELETE", f"/api/notes/{nid}")
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/debug-session")
def debug_session():
    return {
        "session": dict(session)
    }

if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=False)