from flask import Blueprint, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from flask_login import login_user,logout_user,current_user,login_required
from ..db import db
from ..models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile.profile_page'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('profile.profile_page'))
        return "Invalid Credentials", 401

    return render_template('auth.html', active_page='login')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('profile.profile_page'))

    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # password match check
        if password != confirm_password:
            return "Passwords do not match",400

        # duplicate check
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            return "Username or Email already exists",400

        # hash password
        hashed_password = generate_password_hash(password)

        # Get additional fields
        role = request.form.get('role', 'student')
        student_id = request.form.get('student_id')
        graduation_year = request.form.get('graduation_year')
        admin_code = request.form.get('admin_code')

        user = User(
            username=username,
            email=email,
            password=hashed_password,
            role=role,
            student_id=student_id,
            graduation_year=graduation_year,
            admin_code=admin_code
        )

        try:
            db.session.add(user)
            db.session.commit()
            login_user(user)
        except IntegrityError:
            db.session.rollback()
            return "User already exists", 400

        return redirect(url_for('profile.complete_profile'))

    return render_template('auth.html', active_page='signup')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.before_app_request
def update_last_seen():
    from datetime import datetime
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
