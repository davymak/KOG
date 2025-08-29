from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import check_password_hash
from datetime import datetime

from app import db
from models import User, Attendance
from forms import LoginForm

main = Blueprint('main', __name__)

# Liste des dimanches d’août 2025
def get_sundays_august_2025():
    sundays = []
    date = datetime(2025, 8, 1)
    while date.month == 8:
        if date.weekday() == 6:  # 6 = dimanche
            sundays.append(date.strftime("%d/%m/%Y"))
        date = date.replace(day=date.day + 1)
        try:
            date = datetime(2025, 8, date.day)
        except ValueError:
            break
    return sundays

# Page de connexion
@main.route('/', methods=['GET', 'POST'])
@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Identifiants invalides', 'danger')

    return render_template('login.html', form=form)

# Déconnexion
@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

# Tableau de bord
@main.route('/dashboard')
@login_required
def dashboard():
    sundays = get_sundays_august_2025()
    records = Attendance.query.filter_by(user_id=current_user.id).all()
    attendance_data = {r.date: (r.status, r.reason) for r in records}
    return render_template('dashboard.html', sundays=sundays, data=attendance_data)

# Marquer présence
@main.route('/mark', methods=['GET', 'POST'])
@login_required
def mark_attendance():
    sundays = get_sundays_august_2025()

    if request.method == 'POST':
        for date in sundays:
            status = request.form.get(f"status_{date}")
            reason = request.form.get(f"reason_{date}") if status == "A" else None
            record = Attendance.query.filter_by(user_id=current_user.id, date=date).first()
            if record:
                record.status = status
                record.reason = reason
            else:
                new = Attendance(user_id=current_user.id, date=date, status=status, reason=reason)
                db.session.add(new)
        db.session.commit()
        flash("Présence enregistrée avec succès", "success")
        return redirect(url_for('main.dashboard'))

    return render_template('mark_attendance.html', sundays=sundays)

# Résumé hebdomadaire pour l'utilisateur
@main.route('/summary')
@login_required
def summary():
    sundays = get_sundays_august_2025()
    summary_data = []

    for date in sundays:
        total_present = Attendance.query.filter_by(date=date, status='P').count()
        total_absent = Attendance.query.filter_by(date=date, status='A').count()
        total = total_present + total_absent
        rate = (total_absent / total) * 100 if total > 0 else 0
        summary_data.append({
            "date": date,
            "present": total_present,
            "absent": total_absent,
            "rate": round(rate, 2)
        })

    return render_template('summary.html', summary=summary_data)
