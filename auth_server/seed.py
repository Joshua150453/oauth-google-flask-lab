"""Run once: register a demo OAuth client and a demo user."""
from app import create_app
from app.extensions import db
from app.models import OAuthClient, User

DEMO_CLIENT_ID     = "demo-web-client"
DEMO_CLIENT_SECRET = "demo-secret-shhh"

app = create_app()

with app.app_context():
    if not db.session.get(OAuthClient, DEMO_CLIENT_ID):
        c = OAuthClient(
            client_id=DEMO_CLIENT_ID,
            client_secret_hash=OAuthClient.hash_secret(DEMO_CLIENT_SECRET),
            name="Demo Notes Client",
            redirect_uri="http://127.0.0.1:5000/oauth/callback",
            scope="read write",
        )
        db.session.add(c)
        print(f"Registered client {DEMO_CLIENT_ID} / {DEMO_CLIENT_SECRET}")

    if not User.query.filter_by(email="alice@example.com").first():
        u = User(email="alice@example.com", name="Alice Demo")
        u.set_password("alice123")
        db.session.add(u)
        print("Created user alice@example.com / alice123")

    db.session.commit()
    print("Seed done.")