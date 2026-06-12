from datetime import datetime
from urllib.parse import urlencode

from flask import Blueprint, request, redirect, render_template, jsonify, url_for, session

from app.extensions import db
from app.models import OAuthClient, AuthCode, AccessToken
from app.auth import current_user

oauth_bp = Blueprint("oauth", __name__, url_prefix="/oauth")


@oauth_bp.route("/authorize", methods=["GET", "POST"])
def authorize():
    # Required query params
    client_id    = request.args.get("client_id")
    redirect_uri = request.args.get("redirect_uri")
    response_type = request.args.get("response_type")
    scope        = request.args.get("scope", "read")
    state        = request.args.get("state", "")

    if response_type != "code":
        return "unsupported_response_type", 400

    client = db.session.get(OAuthClient, client_id)
    if not client:
        return "unknown client_id", 400
    if client.redirect_uri != redirect_uri:
        return "redirect_uri mismatch", 400

    # Require authenticated user
    user = current_user()
    if user is None:
        return redirect(url_for("auth.login", next=request.url))

    # GET: show consent screen
    if request.method == "GET":
        return render_template("consent.html",
                               client=client, scope=scope,
                               state=state, redirect_uri=redirect_uri)

    # POST: user clicked Approve
    if request.form.get("decision") != "approve":
        return redirect(f"{redirect_uri}?error=access_denied&state={state}")

    code = AuthCode.new(user_id=user.id, client_id=client.client_id,
                        redirect_uri=redirect_uri, scope=scope)
    db.session.add(code)
    db.session.commit()

    qs = urlencode({"code": code.code, "state": state})
    return redirect(f"{redirect_uri}?{qs}")


@oauth_bp.route("/token", methods=["POST"])
def token():
    grant_type    = request.form.get("grant_type")
    code_val      = request.form.get("code")
    redirect_uri  = request.form.get("redirect_uri")
    client_id     = request.form.get("client_id")
    client_secret = request.form.get("client_secret")

    if grant_type != "authorization_code":
        return jsonify({"error": "unsupported_grant_type"}), 400

    client = db.session.get(OAuthClient, client_id)
    if not client or not client.check_secret(client_secret):
        return jsonify({"error": "invalid_client"}), 401

    code = db.session.get(AuthCode, code_val)
    if (not code) or (not code.is_valid()) or code.client_id != client_id \
       or code.redirect_uri != redirect_uri:
        return jsonify({"error": "invalid_grant"}), 400

    # Single-use: mark consumed
    code.used = True

    at = AccessToken.new(user_id=code.user_id, client_id=client_id, scope=code.scope)
    db.session.add(at)
    db.session.commit()

    return jsonify({
        "access_token": at.token,
        "token_type":   "Bearer",
        "expires_in":   int((at.expires_at - datetime.utcnow()).total_seconds()),
        "scope":        at.scope,
    })


@oauth_bp.route("/introspect", methods=["POST"])
def introspect():
    """RFC 7662 — Resource Servers call this to validate a token."""
    token_val = request.form.get("token")
    at = db.session.get(AccessToken, token_val)
    if (not at) or (not at.is_active()):
        return jsonify({"active": False})

    return jsonify({
        "active":    True,
        "sub":       str(at.user_id),
        "client_id": at.client_id,
        "scope":     at.scope,
        "exp":       int(at.expires_at.timestamp()),
        "email":     at.user.email,
        "name":      at.user.name or "",
    })


@oauth_bp.route("/revoke", methods=["POST"])
def revoke():
    at = db.session.get(AccessToken, request.form.get("token"))
    if at:
        at.revoked = True
        db.session.commit()
    return "", 200