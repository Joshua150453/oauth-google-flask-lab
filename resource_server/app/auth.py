import requests
import jwt

from functools import wraps
from flask import request, jsonify, g

from app.extensions import db
from app.models import User

GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"


def verify_google_token(token):
    try:
        # Obtener claves públicas de Google
        jwks = requests.get(GOOGLE_CERTS_URL, timeout=5).json()

        # Leer encabezado del JWT
        header = jwt.get_unverified_header(token)

        key = None
        for k in jwks["keys"]:
            if k["kid"] == header["kid"]:
                key = jwt.algorithms.RSAAlgorithm.from_jwk(k)
                break

        if key is None:
            return None

        claims = jwt.decode(
            token,
            key=key,
            algorithms=["RS256"],
            options={"verify_aud": False}
        )

        return claims

    except Exception as e:
        print("JWT ERROR:", e)
        return None


def require_oauth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")

        if not auth.startswith("Bearer "):
            return jsonify({"error": "missing_bearer_token"}), 401

        token = auth[7:].strip()

        claims = verify_google_token(token)

        if claims is None:
            return jsonify({"error": "invalid_token"}), 401

        sub = claims["sub"]

        user = User.query.filter_by(sub=sub).first()

        if user is None:
            user = User(
                sub=sub,
                email=claims.get("email"),
                name=claims.get("name")
            )

            db.session.add(user)
            db.session.commit()

        g.current_user = user

        # Simulación de scopes para mantener compatibilidad
        g.token_scope = "read write"

        return fn(*args, **kwargs)

    return wrapper


def require_scope(required_scope):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            scopes = (g.token_scope or "").split()

            if required_scope not in scopes:
                return jsonify({
                    "error": "insufficient_scope",
                    "required": required_scope
                }), 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator