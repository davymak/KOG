print("Starting app.py")
import re
import os
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash # Import models AFTER db is initialized to avoid circular imports
from flask_cors import CORS
from extensions import db
from dotenv import load_dotenv
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import User,Member
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import unidecode
import warnings
warnings.simplefilter("ignore")


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
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # route name for login

with app.app_context():
    db.create_all()  # creates tables if they don't exist

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

    return render_template('dashboard.html',welcome_message=welcome_message)

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


# Path to your Excel file
EXCEL_FILE = "TEAM_PAÎTRE.xlsm"

def process_sheet(sheet_index):
    required_cols = ["NOM", "PRENOMS", "N° TELEPHONE", 
                     "DIMANCHE 1", "DIMANCHE 2", "DIMANCHE 3", "DIMANCHE 4", "DIMANCHE 5"]

    df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_index)

    # Keep only required columns that exist in this sheet
    available_cols = [c for c in required_cols if c in df.columns]
    df = df[available_cols]

    # Replace P/A with ✔/✘
    df = df.replace({"P": "✔", "A": "✘"})

    return df.to_dict(orient="records"), available_cols

# Load data once at startup
july_data, july_headers = process_sheet(1)   # Sheet2 (index 1)
august_data, august_headers = process_sheet(2)  # Sheet3 (index 2)

@app.route("/monthly-presence")
def monthly_presence():
    return render_template("monthly-presence.html")

@app.route("/get-presence/<month>")
def get_presence(month):
    if month == "july":
        return jsonify({"headers": july_headers, "rows": july_data})
    elif month == "august":
        return jsonify({"headers": august_headers, "rows": august_data})
    else:
        return jsonify({"error": "Invalid month"}), 400


# Run app
if __name__ == '__main__':
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Database tables created.")
    app.run(debug=True)
