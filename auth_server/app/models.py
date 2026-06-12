import secrets
from datetime import datetime, timedelta
import bcrypt
from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name          = db.Column(db.String(120))
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, pw):
        self.password_hash = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

    def check_password(self, pw):
        return bcrypt.checkpw(pw.encode(), self.password_hash.encode())


class OAuthClient(db.Model):
    __tablename__ = "oauth_clients"

    client_id           = db.Column(db.String(64), primary_key=True)
    client_secret_hash  = db.Column(db.String(255), nullable=False)
    name                = db.Column(db.String(120))
    redirect_uri        = db.Column(db.String(500), nullable=False)
    scope               = db.Column(db.String(255), default="read")

    def check_secret(self, secret):
        return bcrypt.checkpw(secret.encode(), self.client_secret_hash.encode())

    @staticmethod
    def hash_secret(secret):
        return bcrypt.hashpw(secret.encode(), bcrypt.gensalt()).decode()


class AuthCode(db.Model):
    __tablename__ = "auth_codes"

    code         = db.Column(db.String(64), primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    client_id    = db.Column(db.String(64), db.ForeignKey("oauth_clients.client_id"), nullable=False)
    redirect_uri = db.Column(db.String(500), nullable=False)
    scope        = db.Column(db.String(255))
    expires_at   = db.Column(db.DateTime, nullable=False)
    used         = db.Column(db.Boolean, default=False)

    @staticmethod
    def new(user_id, client_id, redirect_uri, scope, ttl_seconds=600):
        return AuthCode(
            code=secrets.token_urlsafe(32),
            user_id=user_id,
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=scope,
            expires_at=datetime.utcnow() + timedelta(seconds=ttl_seconds),
        )

    def is_valid(self):
        return (not self.used) and datetime.utcnow() < self.expires_at


class AccessToken(db.Model):
    __tablename__ = "access_tokens"

    token       = db.Column(db.String(64), primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    client_id   = db.Column(db.String(64), db.ForeignKey("oauth_clients.client_id"), nullable=False)
    scope       = db.Column(db.String(255))
    expires_at  = db.Column(db.DateTime, nullable=False)
    revoked     = db.Column(db.Boolean, default=False)

    user = db.relationship("User")

    @staticmethod
    def new(user_id, client_id, scope, ttl_seconds=3600):
        return AccessToken(
            token=secrets.token_urlsafe(48),
            user_id=user_id,
            client_id=client_id,
            scope=scope,
            expires_at=datetime.utcnow() + timedelta(seconds=ttl_seconds),
        )

    def is_active(self):
        return (not self.revoked) and datetime.utcnow() < self.expires_at