"""
Custom decorators for route protection and access control.
"""

from functools import wraps
from flask import flash, redirect, url_for, abort, request
from flask_login import current_user


def login_required(f):
    """Decorador que requiere que el usuario esté autenticado."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor inicia sesión para acceder a esta página.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*roles):
    """
    Decorador que requiere que el usuario tenga uno de los roles especificados.
    Uso: @role_required('admin', 'root')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Por favor inicia sesión para acceder a esta página.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            if current_user.role not in roles:
                abort(403)  # Forbidden
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def institution_admin_required(f):
    """Decorador que requiere que el usuario sea admin de su institución."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor inicia sesión para acceder a esta página.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.has_any_role('root', 'admin'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def grade_edit_required(f):
    """Decorador que requiere permisos para editar notas."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor inicia sesión para acceder a esta página.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.can_edit_grades():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def student_or_parent_required(f):
    """Decorador que requiere que el usuario sea estudiante o acudiente."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor inicia sesión para acceder a esta página.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.has_any_role('student', 'parent'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
