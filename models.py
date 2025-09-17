from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    #Extract role from username: Admin.Pangni → Admin
    def role(self):
        return self.username.split('.')[0] if '.' in self.username else 'Utilisateur'


    def __init__(self, username, password=None):
        self.username = username.strip()
        if password:
            self.set_password(password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {"id":self.id, "username":self.username}
    
class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.Integer())
    place = db.Column(db.String(100))
    department = db.Column(db.String(100))
    marital_status = db.Column(db.String(50))