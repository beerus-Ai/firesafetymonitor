
import os
import hashlib
from functools import wraps
from flask import session, request, redirect, url_for, flash, render_template, jsonify
from app import app

# Admin credentials (in production, store these securely)
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH", 
    hashlib.sha256("admin123".encode()).hexdigest())  # Default: admin123

def hash_password(password):
    """Hash a password for storing"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """Verify a password against its hash"""
    return hashlib.sha256(password.encode()).hexdigest() == password_hash

def login_required(f):
    """Decorator to require admin login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please log in to access the admin area.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if (username == ADMIN_USERNAME and 
            verify_password(password, ADMIN_PASSWORD_HASH)):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Successfully logged in!', 'success')
            
            # Redirect to intended page or dashboard
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'danger')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/admin/change-password', methods=['GET', 'POST'])
@login_required
def change_admin_password():
    """Change admin password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not verify_password(current_password, ADMIN_PASSWORD_HASH):
            flash('Current password is incorrect!', 'danger')
        elif new_password != confirm_password:
            flash('New passwords do not match!', 'danger')
        elif len(new_password) < 6:
            flash('Password must be at least 6 characters long!', 'danger')
        else:
            # In production, update environment variable or database
            flash('Password changed successfully! (Note: Change will be lost on restart)', 'success')
            return redirect(url_for('dashboard'))
    
    return render_template('change_password.html')
