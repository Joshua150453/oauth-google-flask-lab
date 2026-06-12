from datetime import datetime
from app.extensions import db


class User(db.Model):
    """Local cache of identities — source of truth is the Auth Server."""
    __tablename__ = "users"

    id         = db.Column(db.Integer, primary_key=True)
    sub        = db.Column(db.String(64), unique=True, nullable=False)
    email      = db.Column(db.String(255))
    name       = db.Column(db.String(120))
    first_seen = db.Column(db.DateTime, default=datetime.utcnow)

    notes = db.relationship("Note", backref="owner", cascade="all, delete-orphan")


class Note(db.Model):
    __tablename__ = "notes"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title      = db.Column(db.String(200), nullable=False)
    body       = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":         self.id,
            "title":      self.title,
            "body":       self.body,
            "created_at": self.created_at.isoformat(),
        }