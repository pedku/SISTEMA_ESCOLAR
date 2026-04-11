"""
Authentication routes: login, logout, profile, password change.
"""

from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from extensions import db
from models.user import User
from utils.validators import validate_email

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        if not username or not password:
            flash('Por favor ingrese usuario y contraseña.', 'warning')
            return render_template('login.html')
        
        # Try to find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Su cuenta está desactivada. Contacte al administrador.', 'error')
                return render_template('login.html')
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            login_user(user, remember=remember)
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            flash(f'Bienvenido/a, {user.get_full_name()}!', 'success')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
    
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash('Ha cerrado sesión exitosamente.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile')
@login_required
def profile():
    """Display user profile."""
    return render_template('profile.html')


@auth_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile information."""
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        
        # Validate
        if not first_name or not last_name:
            flash('El nombre y apellido son requeridos.', 'error')
            return redirect(url_for('auth.profile'))
        
        if not validate_email(email):
            flash('El correo electrónico no es válido.', 'error')
            return redirect(url_for('auth.profile'))
        
        # Check if email is already taken by another user
        existing_user = User.query.filter(User.email == email, User.id != current_user.id).first()
        if existing_user:
            flash('El correo electrónico ya está en uso por otro usuario.', 'error')
            return redirect(url_for('auth.profile'))
        
        # Update user
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.email = email
        current_user.phone = phone
        current_user.address = address
        
        # Handle photo upload
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and photo.filename != '':
                # TODO: Implement photo upload logic
                pass
        
        try:
            db.session.commit()
            flash('Perfil actualizado exitosamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el perfil. Intente nuevamente.', 'error')
            current_app.logger.error(f'Error updating profile: {e}')
        
        return redirect(url_for('auth.profile'))
    
    return redirect(url_for('auth.profile'))


@auth_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    """Change user password."""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate
        if not current_password or not new_password or not confirm_password:
            flash('Todos los campos son requeridos.', 'error')
            return redirect(url_for('auth.profile'))
        
        if not current_user.check_password(current_password):
            flash('La contraseña actual es incorrecta.', 'error')
            return redirect(url_for('auth.profile'))
        
        if new_password != confirm_password:
            flash('Las contraseñas nuevas no coinciden.', 'error')
            return redirect(url_for('auth.profile'))
        
        if len(new_password) < 6:
            flash('La nueva contraseña debe tener al menos 6 caracteres.', 'warning')
            return redirect(url_for('auth.profile'))
        
        # Update password
        current_user.password_hash = generate_password_hash(new_password)
        
        try:
            db.session.commit()
            flash('Contraseña actualizada exitosamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar la contraseña. Intente nuevamente.', 'error')
            current_app.logger.error(f'Error changing password: {e}')
        
        return redirect(url_for('auth.profile'))
    
    return redirect(url_for('auth.profile'))
