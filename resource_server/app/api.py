from flask import Blueprint, request, jsonify, g

from app.extensions import db
from app.models import Note
from app.auth import require_oauth, require_scope

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/me", methods=["GET"])
@require_oauth
def me():
    u = g.current_user
    return jsonify({
        "id":    u.id,
        "sub":   u.sub,
        "email": u.email,
        "name":  u.name,
        "scope": g.token_scope,
    })


@api_bp.route("/notes", methods=["GET"])
@require_oauth
@require_scope("read")
def list_notes():
    items = Note.query.filter_by(user_id=g.current_user.id).all()
    return jsonify([n.to_dict() for n in items])


@api_bp.route("/notes", methods=["POST"])
@require_oauth
@require_scope("write")
def create_note():
    data = request.get_json() or {}
    if not data.get("title"):
        return jsonify({"error": "title required"}), 400

    n = Note(user_id=g.current_user.id,
             title=data["title"],
             body=data.get("body", ""))
    db.session.add(n)
    db.session.commit()
    return jsonify(n.to_dict()), 201


@api_bp.route("/notes/<int:nid>", methods=["DELETE"])
@require_oauth
@require_scope("write")
def delete_note(nid):
    n = Note.query.filter_by(id=nid, user_id=g.current_user.id).first_or_404()
    db.session.delete(n)
    db.session.commit()
    return "", 204