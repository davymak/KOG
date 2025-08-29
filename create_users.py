from app import create_app, db
from models import User
from werkzeug.security import generate_password_hash

# Créer l'app et activer le contexte
app = create_app()
app.app_context().push()

# Liste des utilisateurs à créer
users = [
    {"username": "alice", "password": "pass123"},
    {"username": "bob", "password": "pass123"},
    {"username": "charlie", "password": "pass123"},
    {"username": "david", "password": "pass123"},
    {"username": "eve", "password": "pass123"},
]

# Création dans la base
for u in users:
    if not User.query.filter_by(username=u["username"]).first():
        user = User(
            username=u["username"],
            password=generate_password_hash(u["password"])
        )
        db.session.add(user)

db.session.commit()
print("✅ 5 utilisateurs créés avec succès.")
