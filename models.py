from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

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
    phone = db.Column(db.String(20))
    place = db.Column(db.String(100))
    department = db.Column(db.String(100))
    marital_status = db.Column(db.String(50))

class ActiveMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=True)  # optional link to Member
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "category": self.category,
        }
    


#Database Full Members List
class FullMember(db.Model):
    __tablename__ = "full_members_list"
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100))
    prenoms = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    departement = db.Column(db.String(100))

    def __repr__(self):
        return f"<Member {self.nom} {self.prenoms}>"    



# en haut de models.py si besoin
from datetime import datetime

class SundayPresence(db.Model):
    __tablename__ = "sunday_presence"
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    sunday_date = db.Column(db.Date, nullable=False, index=True)
    present = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('member_id','sunday_date', name='u_member_sunday'),)

    def __repr__(self):
        return f"<SundayPresence member={self.member_id} date={self.sunday_date} present={self.present}>"


