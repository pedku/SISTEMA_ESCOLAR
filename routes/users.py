"""
User management routes.
Full CRUD for root (all users across all institutions)
and for admin (users scoped to their institution only).
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models.user import User
from models.institution import Institution, Campus
from models.academic import AcademicStudent
from utils.decorators import role_required
from utils.institution_resolver import get_current_institution
from utils.username_generator import generate_username
from werkzeug.security import generate_password_hash
from datetime import datetime
import re

users_bp = Blueprint('users', __name__)


# ============================================
# User List
# ============================================

@users_bp.route('/users')
@login_required
@role_required('root', 'admin')
def users_list():
    """List users - root sees all, admin sees only their institution."""
    institution = get_current_institution()
    
    # Base query
    query = User.query
    
    # Admin can only see users from their institution
    if not current_user.is_root():
        if institution:
            query = query.filter(User.institution_id == institution.id)
        else:
            flash('No tiene una institución asignada.', 'error')
            return redirect(url_for('dashboard.index'))
    
    # Apply filters
    role = request.args.get('role', '')
    search = request.args.get('search', '').strip()
    
    if role:
        query = query.filter(User.role == role)
    
    if search:
        query = query.filter(
            db.or_(
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%'),
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )
    
    # Order by role hierarchy then name
    query = query.order_by(
        User.role,
        User.first_name,
        User.last_name
    )
    
    users = query.all()
    
    # Statistics
    stats = {
        'total': len(users),
        'root': sum(1 for u in users if u.role == 'root'),
        'admin': sum(1 for u in users if u.role == 'admin'),
        'coordinator': sum(1 for u in users if u.role == 'coordinator'),
        'teacher': sum(1 for u in users if u.role == 'teacher'),
        'student': sum(1 for u in users if u.role == 'student'),
        'parent': sum(1 for u in users if u.role == 'parent'),
        'viewer': sum(1 for u in users if u.role == 'viewer'),
    }
    
    return render_template(
        'users/list.html',
        users=users,
        stats=stats,
        filters={'role': role, 'search': search}
    )


# ============================================
# Create User
# ============================================

@users_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin')
def user_create():
    """Create a new user."""
    institution = get_current_institution()
    
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        document_type = request.form.get('document_type', 'CC')
        document_number = request.form.get('document_number', '').strip()
        role = request.form.get('role', '').strip()
        institution_id = request.form.get('institution_id', type=int)
        
        # Validation
        if not first_name or not last_name or not email or not role:
            flash('Nombre, apellido, email y rol son obligatorios.', 'error')
            institutions = Institution.query.order_by(Institution.name).all() if current_user.is_root() else [institution]
            return render_template('users/create.html', institutions=institutions, user=None, 
                                   form_data=request.form)
        
        if not document_number:
            flash('El número de documento es obligatorio (se usa como contraseña inicial).', 'error')
            institutions = Institution.query.order_by(Institution.name).all() if current_user.is_root() else [institution]
            return render_template('users/create.html', institutions=institutions, user=None,
                                   form_data=request.form)
        
        # Auto-generate username from name and document
        existing_users = User.query.all()
        existing_usernames = [u.username for u in existing_users]
        username = generate_username(first_name, last_name, document_number, existing_usernames)
        
        # Validate email format
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash('El correo electrónico no tiene un formato válido.', 'error')
            institutions = Institution.query.order_by(Institution.name).all() if current_user.is_root() else [institution]
            return render_template('users/create.html', institutions=institutions, user=None,
                                   form_data=request.form)
        
        # Check email uniqueness
        if User.query.filter_by(email=email).first():
            flash('El correo electrónico ya está registrado.', 'error')
            institutions = Institution.query.order_by(Institution.name).all() if current_user.is_root() else [institution]
            return render_template('users/create.html', institutions=institutions, user=None,
                                   form_data=request.form)
        
        # Institution assignment
        if current_user.is_root():
            final_institution_id = institution_id
        else:
            final_institution_id = institution.id if institution else None
        
        # Default password = document number
        default_password = document_number.strip()
        
        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(default_password),
            first_name=first_name,
            last_name=last_name,
            role=role,
            institution_id=final_institution_id,
            document_type=document_type,
            document_number=document_number,
            phone=request.form.get('phone', '').strip() or None,
            address=request.form.get('address', '').strip() or None,
            department=request.form.get('department', '').strip() or None,
            municipality=request.form.get('municipality', '').strip() or None,
            country=request.form.get('country', 'Colombia'),
            must_change_password=True,  # Force password change on first login
            is_active=True
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # If creating a student, create academic student record
            if role == 'student':
                flash(f'Usuario creado exitosamente. Username: {username}. Complete el perfil académico.', 'info')
                return redirect(url_for('students.new', user_id=user.id))
            
            flash(f'✅ Usuario creado exitosamente.\n\n👤 Username: {username}\n🔑 Contraseña inicial: {document_number}\n\n⚠️ El usuario deberá cambiar la contraseña en su primer inicio de sesión.', 'success')
            return redirect(url_for('users.users_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el usuario: {str(e)}', 'error')
            institutions = Institution.query.order_by(Institution.name).all() if current_user.is_root() else [institution]
            return render_template('users/create.html', institutions=institutions, user=None,
                                   form_data=request.form, generated_username=username)
    
    # GET request
    institutions = Institution.query.order_by(Institution.name).all() if current_user.is_root() else [institution]
    
    return render_template('users/create.html', institutions=institutions, user=None)


# ============================================
# Edit User
# ============================================

@users_bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin')
def user_edit(id):
    """Edit an existing user."""
    user = User.query.get_or_404(id)
    institution = get_current_institution()
    
    # Verify access - admin can only edit users from their institution
    if not current_user.is_root():
        if user.institution_id != (institution.id if institution else None):
            flash('No tiene permiso para editar este usuario.', 'error')
            return redirect(url_for('users.users_list'))
    
    # Root cannot edit other root users' details (except themselves)
    if user.role == 'root' and user.id != current_user.id:
        if current_user.is_root():
            flash('No puede editar otros usuarios root.', 'warning')
            return redirect(url_for('users.users_list'))
    
    if request.method == 'POST':
        user.first_name = request.form.get('first_name', '').strip()
        user.last_name = request.form.get('last_name', '').strip()
        user.email = request.form.get('email', '').strip()
        user.document_type = request.form.get('document_type', 'CC')
        user.document_number = request.form.get('document_number', '').strip() or None
        user.phone = request.form.get('phone', '').strip() or None
        user.address = request.form.get('address', '').strip() or None
        
        # Only root can change role
        if current_user.is_root():
            new_role = request.form.get('role', '').strip()
            if new_role and new_role != user.role:
                # Prevent demoting other root users
                if user.role == 'root' and user.id != current_user.id:
                    flash('No puede cambiar el rol de otro usuario root.', 'error')
                else:
                    user.role = new_role
        
        # Only root can change institution
        if current_user.is_root():
            new_institution_id = request.form.get('institution_id', type=int)
            user.institution_id = new_institution_id
        
        # Change password if provided
        new_password = request.form.get('new_password', '').strip()
        if new_password:
            if len(new_password) < 6:
                flash('La contraseña debe tener al menos 6 caracteres.', 'error')
                institutions = Institution.query.order_by(Institution.name).all() if current_user.is_root() else [institution]
                return render_template('users/edit.html', user=user, institutions=institutions)
            user.password_hash = generate_password_hash(new_password)
        
        # Toggle active status (only root or admin for non-root users)
        if user.role != 'root':
            is_active = request.form.get('is_active') == 'on'
            user.is_active = is_active
        
        try:
            db.session.commit()
            flash('Usuario actualizado exitosamente.', 'success')
            return redirect(url_for('users.users_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'error')
    
    institutions = Institution.query.order_by(Institution.name).all() if current_user.is_root() else [institution]
    return render_template('users/edit.html', user=user, institutions=institutions)


# ============================================
# Delete User
# ============================================

@users_bp.route('/users/<int:id>/delete', methods=['POST'])
@login_required
@role_required('root', 'admin')
def user_delete(id):
    """Delete a user."""
    user = User.query.get_or_404(id)
    institution = get_current_institution()
    
    # Verify access
    if not current_user.is_root():
        if user.institution_id != (institution.id if institution else None):
            flash('No tiene permiso para eliminar este usuario.', 'error')
            return redirect(url_for('users.users_list'))
    
    # Cannot delete root users
    if user.role == 'root':
        flash('No se pueden eliminar usuarios root.', 'error')
        return redirect(url_for('users.users_list'))
    
    # Cannot delete self
    if user.id == current_user.id:
        flash('No puede eliminar su propio usuario.', 'error')
        return redirect(url_for('users.users_list'))
    
    # Check for related data
    if user.role == 'teacher':
        from models.academic import SubjectGrade
        has_classes = SubjectGrade.query.filter_by(teacher_id=user.id).first()
        if has_classes:
            flash('No se puede eliminar el profesor porque tiene asignaturas asignadas.', 'warning')
            return redirect(url_for('users.users_list'))
    
    if user.role == 'coordinator':
        from models.academic import Grade
        is_director = Grade.query.filter_by(director_id=user.id).first()
        if is_director:
            flash('No se puede eliminar el coordinador porque es director de grado.', 'warning')
            return redirect(url_for('users.users_list'))
    
    if user.role == 'student':
        academic_student = AcademicStudent.query.filter_by(user_id=user.id).first()
        if academic_student:
            if academic_student.grade_records.count() > 0 or academic_student.attendance_records.count() > 0:
                flash('No se puede eliminar el estudiante porque tiene registros académicos.', 'warning')
                return redirect(url_for('users.users_list'))
            # Delete academic student record
            db.session.delete(academic_student)
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash('Usuario eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {str(e)}', 'error')
    
    return redirect(url_for('users.users_list'))


# ============================================
# Bulk Operations
# ============================================

@users_bp.route('/users/import-excel', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin')
def users_import_excel():
    """Import users from Excel file."""
    if request.method == 'GET':
        return render_template('users/import_excel.html')
    
    # POST - handle file upload
    if 'file' not in request.files:
        flash('No se seleccionó ningún archivo.', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No se seleccionó ningún archivo.', 'error')
        return redirect(request.url)
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        flash('Solo se permiten archivos Excel (.xlsx, .xls)', 'error')
        return redirect(request.url)
    
    try:
        import pandas as pd
        import io
        
        # Read Excel
        df = pd.read_excel(io.BytesIO(file.read()))
        
        # Expected columns: username, email, password, first_name, last_name, role
        required_cols = ['username', 'email', 'password', 'first_name', 'last_name', 'role']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            flash(f'Faltan columnas en el archivo: {", ".join(missing_cols)}', 'error')
            return redirect(request.url)
        
        institution = get_current_institution()
        created = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                # Check if username exists
                if User.query.filter_by(username=str(row['username']).strip()).first():
                    errors.append(f"Fila {idx + 2}: Usuario '{row['username']}' ya existe")
                    continue
                
                # Check if email exists
                if User.query.filter_by(email=str(row['email']).strip()).first():
                    errors.append(f"Fila {idx + 2}: Email '{row['email']}' ya existe")
                    continue
                
                user = User(
                    username=str(row['username']).strip(),
                    email=str(row['email']).strip(),
                    password_hash=generate_password_hash(str(row['password'])),
                    first_name=str(row['first_name']).strip(),
                    last_name=str(row['last_name']).strip(),
                    role=str(row['role']).strip().lower(),
                    institution_id=institution.id if institution and not current_user.is_root() else None,
                    is_active=True
                )
                
                db.session.add(user)
                created += 1
                
            except Exception as e:
                errors.append(f"Fila {idx + 2}: {str(e)}")
        
        db.session.commit()
        
        if errors:
            flash(f'{created} usuarios creados, {len(errors)} errores. Ver logs para detalles.', 'warning')
        else:
            flash(f'{created} usuarios importados exitosamente.', 'success')
        
        return render_template('users/import_excel.html', created=created, errors=errors)
        
    except Exception as e:
        flash(f'Error al procesar el archivo: {str(e)}', 'error')
        return redirect(request.url)


# ============================================
# API Endpoints
# ============================================

@users_bp.route('/users/api/check-username')
@login_required
def check_username():
    """Check if username is available (AJAX)."""
    username = request.args.get('username', '')
    available = not User.query.filter_by(username=username).first()
    return jsonify({'available': available})


@users_bp.route('/users/api/check-email')
@login_required
def check_email():
    """Check if email is available (AJAX)."""
    email = request.args.get('email', '')
    available = not User.query.filter_by(email=email).first()
    return jsonify({'available': available})
