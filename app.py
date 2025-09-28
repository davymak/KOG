print("Starting app.py")
import re
import os
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash # Import models AFTER db is initialized to avoid circular imports
from flask_cors import CORS
from extensions import db
from dotenv import load_dotenv
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import User,Member,ActiveMember
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import unidecode
import warnings
import calendar
from datetime import date, timedelta, datetime 
warnings.simplefilter("ignore")
from flask_migrate import Migrate
from models import SundayPresence


ROLE_MAPPING = {
    "Admin": "Administratrice",
    "Pr": "Prophète",
    "Membre": "Excellence"
}


# Load env variables from .env file
load_dotenv()  

#Initialize app
app = Flask(__name__)
# Set config AFTER creating app
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///yourdb.db')  
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'e6be03ebb51af7d5195d51be02bb1f7d983b14f80cdade1b2b820b1c91e5f926')  # fallback for dev


# Initialize extensions with app
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # route name for login

#with app.app_context():
    #db.create_all()#  # creates tables if they don't exist
with app.app_context():
    db.create_all()
    

#Enable CORS
CORS(app)

#User loader for flask-login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#Security for email and Password (Layer of security, minimum of characters and lenght)
def is_strong_password(password):
    """Check password strength: min 8 chars, at least 1 letter and 1 number."""
    if len(password) < 8:
        return False
    if not re.search(r'[A-Za-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    return True

def is_valid_username(username):
    #Validates username in the format Role.Name
    #Role: letters only, starting with uppercase
    #Name: letters only, starting with uppercase
    #Example: Admin.Pangni
    pattern = r'^[A-Z][a-zA-Z]*\.[a-zA-Z][a-zA-Z]*$'
    return re.match(pattern, username) is not None

# Homepage route
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

#login route
@app.route('/login', methods=['GET','POST'])
def login():
    print("Request method:", request.method)
    print("Form data:", request.form)
    print("JSON data:", request.get_json(silent=True))
    if current_user.is_authenticated:
                return redirect(url_for('dashboard'))

        # Initialize variables safely
    username = None
    password = None

    if request.method == 'POST':
        if request.is_json:
            data = request.get_json(silent=True)  # silent=True avoids exceptions
            if data:
                username = data.get('username')
                password = data.get('password')
        else:
            username = request.form.get('username')
            password = request.form.get('password')
        

        if not username or not password:
            flash('Username and password are required')
            return redirect(url_for('login'))
                
                # Normalize username input
        username = username.strip()

        user = User.query.filter_by(username=username).first() #Find user by username
                #Verify Password       
        if user and user.check_password(password):
            login_user(user)
            flash("Connexion Réussie")
            return redirect(url_for("dashboard"))  # 👈 redirect to dashboard
        else:
            flash('Invalid Username or Password')
            return render_template('login.html')
    return render_template('login.html') 

    
# User route
# Identification required (Username, email, password required or not)
@app.route('/add_user', methods=['GET','POST'])
def add_user():
    if request.method == 'GET':
        return render_template('add_user.html')  # show the registration form
        
    data = request.get_json(force=True)
    print("Received data:",data)
        
    if not data:
            return jsonify({'error': 'JSON data required'}), 400

# Trim whitespace and normalize
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
            return jsonify({'error': 'Username and Password are required'}), 400  

    if len(username.strip()) < 2:
            return jsonify({'error': 'UserName must be at least 2 characters long'}), 400

    if not is_strong_password(password):
            return jsonify({'error': 'Password must be at least 8 characters long and contain letters and numbers'}), 400
    
    # In your add_user route, after trimming username:
    if not is_valid_username(username):
            return jsonify({'error': "Username must be in the format Role.Name, e.g., 'Admin.Pangni'"}), 400

    # Check for duplicate username
    if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already registered'}), 400
    try:
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        # Auto login the new user
        login_user(new_user)
        flash("Connexion Réussie")
        return jsonify({"redirect": url_for("dashboard")})    
    except Exception as e:
        db.session.rollback()
        print("DB ERROR:", e)
        return jsonify({'error':'Database error','details': str(e)}),500

# Dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
    username = current_user.username  # e.g., "Admin.Pangni"
    role_short, name = username.split(".")  # ["Admin", "Pangni"]
    role_full = ROLE_MAPPING.get(role_short, role_short)  # fallback to short if not found
    welcome_message = f"Bienvenue {role_full}"  # "Bienvenue Administratrice"

    return render_template('dashboard.html',role_full=role_full)

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

#full-members-list
@app.route("/full_members_list")
@login_required
def full_members_list():
    members = Member.query.all()
    return render_template("full_members_list.html",members=members)

@app.route("/add-member", methods=["POST"])
def add_member():
    data = request.json
    member = Member(
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone=data.get("phone", ""),
        place=data.get("place", ""),
        department=data.get("department", ""),
        marital_status=data.get("marital_status", "")
    )
    db.session.add(member)
    db.session.commit()
    return {"success": True, "id": member.id}


@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([
    {
         "id": u.id, 
         "username": u.username,
         "password_hash":u.password_hash
    }
for u in users
    ])

@app.route("/update-member/<int:id>", methods=["POST"])
@login_required
def update_member(id):
    data = request.json
    member = Member.query.get(id)
    if not member:
        return jsonify({"success": False, "error": "Member not found"}), 404

    member.first_name = data["first_name"]
    member.last_name = data["last_name"]
    member.phone = data.get("phone", "")
    member.place = data.get("place", "")
    member.department = data.get("department", "")
    member.marital_status = data.get("marital_status", "")

    db.session.commit()
    return jsonify({"success": True})

@app.route("/delete-member/<int:id>", methods=["POST"])
@login_required
def delete_member(id):
    member = Member.query.get(id)
    if not member:
        return jsonify({"success": False, "error": "Membre non trouvé"}), 404
    try:
        db.session.delete(member)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)})

#active_members
@app.route("/active_members")
@login_required
def active_members():
    members = ActiveMember.query.all()
    return render_template("active_members.html",members=members)

# Add a new ActiveMember
@app.route("/add-active-member", methods=["POST"])
@login_required
def add_active_member():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data sent"}), 400

    try:
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        phone = data.get("phone")
        category = data.get("category", "Active Base")

        # Create new ActiveMember
        new_member = ActiveMember(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            category=category
        )
        db.session.add(new_member)
        db.session.commit()

        return jsonify({"success": True, "member": new_member.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


# Update ActiveMember
@app.route("/update-active-member/<int:id>", methods=["PUT"])
@login_required
def update_active_member(id):
    member = ActiveMember.query.get_or_404(id)
    data = request.json
    member.first_name = data["first_name"]
    member.last_name = data["last_name"]
    member.phone = data["phone"]
    member.category = data["category"]
    db.session.commit()
    return jsonify(member.to_dict())

# Delete ActiveMember
@app.route("/delete-active-member/<int:id>", methods=["DELETE"])
@login_required
def delete_active_member(id):
    member = ActiveMember.query.get_or_404(id)
    db.session.delete(member)
    db.session.commit()
    return jsonify({"message": "Deleted"})

#sleeping_members
@app.route("/sleeping_members")
@login_required
def sleeping_members():
    members = Member.query.all()  # assuming you have 'active' column
    return render_template("sleeping_members.html", members=[])    


@app.route("/monthly-presence")
def monthly_presence():
    today = date.today()
    months = []

    # Generate the next 6 months (including current month)
    for i in range(6):
        # Get year and month after i months
        year = (today.year + (today.month + i - 1) // 12)
        month = (today.month + i - 1) % 12 + 1

        month_name = calendar.month_name[month]

        # Count Sundays
        sundays = sum(1 for day in range(1, calendar.monthrange(year, month)[1] + 1)
                      if date(year, month, day).weekday() == 6)

        months.append({
            "name": f"{month_name} {year}",
            "sundays": sundays
        })

    return render_template("monthly-presence.html", months=months)


@app.route("/sunday_presence")
@login_required
def sunday_presence():
    today = date.today()
    months = []

    # Generate next 6 months
    for i in range(6):
        year = (today.year + (today.month + i - 1) // 12)
        month = (today.month + i - 1) % 12 + 1
        month_name = calendar.month_name[month]
        months.append((year, month, month_name))

    members = Member.query.all()
    return render_template(
        "sunday_presence.html",
        members=members,
        current_year=today.year,
        current_month=today.month,
        months=months
    )


@app.route("/save-presence", methods=["POST"])
@login_required
def save_presence():
    data = request.get_json(silent=True)
    if not data:
        return jsonify(success=False, error="No JSON payload"), 400

    sunday = data.get("sunday")
    members = data.get("members")  # attendu: { "<member_id>": true/false, ... }

    if not sunday or not isinstance(members, dict):
        return jsonify(success=False, error="Missing 'sunday' or 'members'"), 400

    try:
        sunday_date = datetime.strptime(sunday, "%Y-%m-%d").date()
    except Exception:
        return jsonify(success=False, error="Bad date format, expected YYYY-MM-DD"), 400

    try:
        for member_id_str, present_val in members.items():
            try:
                member_id = int(member_id_str)
            except Exception:
                continue

            rec = SundayPresence.query.filter_by(member_id=member_id, sunday_date=sunday_date).first()
            if rec:
                rec.present = bool(present_val)
            else:
                db.session.add(
                    SundayPresence(member_id=member_id, sunday_date=sunday_date, present=bool(present_val))
                )
        db.session.commit()
        return jsonify(success=True)
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, error=str(e)), 500


@app.route("/get-presence")
@login_required
def get_presence():
    sunday = request.args.get("sunday")
    if not sunday:
        return jsonify({})

    try:
        sunday_date = datetime.strptime(sunday, "%Y-%m-%d").date()
    except Exception:
        return jsonify({})

    rows = SundayPresence.query.filter_by(sunday_date=sunday_date).all()
    # renvoie un mapping: { "member_id": true/false, ... }
    result = { str(r.member_id): r.present for r in rows }
    return jsonify(result)



@app.route("/reports")
def reports():
    return render_template("reports.html")

@app.route("/monthly-data")
def monthly_data_api():
    # Compute monthly presence/absence counts
    # Example: group by sunday_date
    from collections import defaultdict
    data = defaultdict(lambda: {"present": 0, "absent": 0})

    all_records = SundayPresence.query.all()
    for r in all_records:
        if r.present:
            data[str(r.sunday_date)]["present"] += 1
        else:
            data[str(r.sunday_date)]["absent"] += 1

    # Sort by date
    sorted_data = dict(sorted(data.items()))
    return jsonify(sorted_data)


# Run app
if __name__ == '__main__':
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Database tables created.")
    app.run(debug=True)
