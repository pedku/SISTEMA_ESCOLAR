"""
Institution management routes.
Full CRUD for institution, campuses, grades, subjects, periods, and evaluation criteria.
Includes multi-institution management for root users.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, session
from flask_login import login_required, current_user
from extensions import db
from models.institution import Institution, Campus
from models.academic import Grade, Subject, SubjectGrade
from models.grading import AcademicPeriod, GradeCriteria
from models.user import User
from utils.decorators import role_required
from utils.institution_resolver import (
    get_current_institution, filter_by_institution, 
    get_institution_grades, get_institution_subjects
)
from datetime import datetime
import os
import re

institution_bp = Blueprint('institution', __name__)


# ============================================
# Multi-Institution Management (Root Only)
# ============================================

@institution_bp.route('/list')
@login_required
@role_required('root')
def institutions_list():
    """List all institutions - root only."""
    all_institutions = Institution.query.order_by(Institution.name).all()
    return render_template('institution/institutions_list.html', institutions=all_institutions)


@institution_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required('root')
def institution_new():
    """Create a new institution - root only."""
    form_data = {}
    errors = {}

    if request.method == 'POST':
        # Collect all form data
        form_data = {
            'name': request.form.get('name', '').strip(),
            'nit': request.form.get('nit', '').strip(),
            'address': request.form.get('address', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'email': request.form.get('email', '').strip(),
            'municipality': request.form.get('municipality', '').strip(),
            'department': request.form.get('department', '').strip(),
            'resolution': request.form.get('resolution', '').strip(),
            'academic_year': request.form.get('academic_year', '2026').strip(),
            'admin_first_name': request.form.get('admin_first_name', '').strip(),
            'admin_last_name': request.form.get('admin_last_name', '').strip(),
            'admin_email': request.form.get('admin_email', '').strip(),
            'admin_document': request.form.get('admin_document', '').strip(),
            'admin_document_type': request.form.get('admin_document_type', 'CC').strip(),
            'admin_phone': request.form.get('admin_phone', '').strip(),
        }

        name = form_data['name']
        nit = form_data['nit']

        if not name:
            errors['general'] = 'El nombre de la institución es obligatorio.'
            flash('❌ El nombre de la institución es obligatorio.', 'error')
            return render_template('institution/institution_form.html', institution=None, form_data=form_data, errors=errors)

        # Check for duplicate NIT if provided
        if nit:
            existing = Institution.query.filter_by(nit=nit).first()
            if existing:
                errors['nit'] = 'Ya existe una institución con ese NIT.'
                flash('❌ Ya existe una institución con ese NIT.', 'error')
                return render_template('institution/institution_form.html', institution=None, form_data=form_data, errors=errors)

        institution = Institution(
            name=name,
            nit=nit if nit else None,
            address=form_data['address'],
            phone=form_data['phone'],
            email=form_data['email'],
            municipality=form_data['municipality'],
            department=form_data['department'],
            resolution=form_data['resolution'],
            academic_year=form_data['academic_year']
        )

        # Handle logo upload
        if 'logo' in request.files:
            logo_file = request.files['logo']
            if logo_file and logo_file.filename != '':
                # Validate file extension
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                file_ext = logo_file.filename.rsplit('.', 1)[1].lower() if '.' in logo_file.filename else ''
                if file_ext in allowed_extensions:
                    # Create unique filename
                    import uuid
                    logo_filename = f"logo_{uuid.uuid4().hex}.{file_ext}"
                    upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
                    logo_path = os.path.join(upload_dir, 'logos', logo_filename)
                    os.makedirs(os.path.dirname(logo_path), exist_ok=True)
                    logo_file.save(logo_path)
                    institution.logo = os.path.join('logos', logo_filename)

        try:
            db.session.add(institution)
            db.session.flush()  # Get institution.id without committing

            # Admin creation is MANDATORY - only basic data required
            admin_first_name = form_data['admin_first_name']
            admin_last_name = form_data['admin_last_name']
            admin_email = form_data['admin_email']
            admin_document = form_data['admin_document']

            # Validate required fields
            if not all([admin_first_name, admin_last_name, admin_email, admin_document]):
                db.session.rollback()
                errors['general'] = 'Es obligatorio crear un administrador: Nombre, Apellido, Email y Documento son requeridos.'
                flash('❌ Es obligatorio crear un administrador: Nombre, Apellido, Email y Documento son requeridos.', 'error')
                return render_template('institution/institution_form.html', institution=None, form_data=form_data, errors=errors)

            from werkzeug.security import generate_password_hash
            from utils.username_generator import generate_username, generate_username_from_db

            # Auto-generate username using new dynamic system
            admin_username = generate_username_from_db(
                admin_first_name,
                admin_last_name,
                query_func=lambda pattern: [
                    u.username for u in User.query.filter(
                        User.username.like(f'{pattern}%')
                    ).all()
                ]
            )

            # Default password = document number
            default_password = admin_document.strip()

            # Check if email already exists
            if User.query.filter_by(email=admin_email).first():
                db.session.rollback()
                errors['admin_email'] = f'El email "{admin_email}" ya está registrado.'
                flash(f'❌ El email "{admin_email}" ya está registrado.', 'error')
                return render_template('institution/institution_form.html', institution=None,
                                       form_data=form_data, errors=errors,
                                       generated_username=admin_username)

            # Create admin user with auto-generated username
            admin_user = User(
                username=admin_username,
                email=admin_email,
                password_hash=generate_password_hash(default_password),
                first_name=admin_first_name,
                last_name=admin_last_name,
                role='admin',
                institution_id=institution.id,
                document_type=form_data['admin_document_type'],
                document_number=admin_document,
                phone=form_data['admin_phone'] or None,
                country='Colombia',
                must_change_password=True,  # Force password change on first login
                is_active=True
            )
            db.session.add(admin_user)
            db.session.commit()

            flash(f'✅ Institución "{institution.name}" creada exitosamente.\n\n👤 Admin: {admin_username}\n🔑 Contraseña: {default_password}\n\n⚠️ El admin deberá cambiar la contraseña en su primer inicio de sesión.', 'success')
            return redirect(url_for('institution.institutions_list'))
        except Exception as e:
            db.session.rollback()
            errors['general'] = f'Error al crear la institución: {str(e)}'
            flash(f'❌ Error al crear la institución: {str(e)}', 'error')

    return render_template('institution/institution_form.html', institution=None, form_data={}, errors={})


@institution_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('root')
def institution_edit(id):
    """Edit an existing institution - root only."""
    institution = db.session.get(Institution, id)

    if not institution:
        flash('Institución no encontrada.', 'error')
        return redirect(url_for('institution.institutions_list'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        nit = request.form.get('nit', '').strip()

        if not name:
            flash('El nombre de la institución es obligatorio.', 'error')
            return render_template('institution/institution_form.html', institution=institution)

        # Check for duplicate NIT if changed
        if nit and nit != institution.nit:
            existing = Institution.query.filter_by(nit=nit).first()
            if existing:
                flash('Ya existe otra institución con ese NIT.', 'error')
                return render_template('institution/institution_form.html', institution=institution)

        institution.name = name
        institution.nit = nit if nit else None
        institution.address = request.form.get('address', '').strip()
        institution.phone = request.form.get('phone', '').strip()
        institution.email = request.form.get('email', '').strip()
        institution.municipality = request.form.get('municipality', '').strip()
        institution.department = request.form.get('department', '').strip()
        institution.resolution = request.form.get('resolution', '').strip()
        institution.academic_year = request.form.get('academic_year', '2026').strip()

        # Handle logo upload
        if 'logo' in request.files:
            logo_file = request.files['logo']
            if logo_file and logo_file.filename != '':
                # Validate file extension
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                file_ext = logo_file.filename.rsplit('.', 1)[1].lower() if '.' in logo_file.filename else ''
                if file_ext in allowed_extensions:
                    # Delete old logo if exists
                    if institution.logo:
                        old_logo_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), institution.logo)
                        if os.path.exists(old_logo_path):
                            os.remove(old_logo_path)

                    # Save new logo
                    import uuid
                    logo_filename = f"logo_{uuid.uuid4().hex}.{file_ext}"
                    upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
                    logo_path = os.path.join(upload_dir, 'logos', logo_filename)
                    os.makedirs(os.path.dirname(logo_path), exist_ok=True)
                    logo_file.save(logo_path)
                    institution.logo = os.path.join('logos', logo_filename)

        try:
            db.session.commit()
            flash('Institución actualizada exitosamente.', 'success')
            return redirect(url_for('institution.institutions_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar la institución: {str(e)}', 'error')

    return render_template('institution/institution_form.html', institution=institution)


@institution_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@role_required('root')
def institution_delete(id):
    """Delete an institution - root only."""
    institution = db.session.get(Institution, id)

    if not institution:
        flash('Institución no encontrada.', 'error')
        return redirect(url_for('institution.institutions_list'))

    # Check for related data
    has_campuses = institution.campuses.count() > 0
    has_periods = institution.academic_periods.count() > 0
    has_criteria = institution.grade_criteria.count() > 0
    has_students = institution.academic_students.count() > 0

    if has_campuses or has_periods or has_criteria or has_students:
        flash(
            'No se puede eliminar la institución porque tiene datos asociados '
            '(sedes, periodos, criterios de evaluación o estudiantes).',
            'warning'
        )
        return redirect(url_for('institution.institutions_list'))

    # Delete logo file if exists
    if institution.logo:
        logo_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), institution.logo)
        if os.path.exists(logo_path):
            os.remove(logo_path)

    try:
        db.session.delete(institution)
        db.session.commit()
        flash('Institución eliminada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la institución: {str(e)}', 'error')

    return redirect(url_for('institution.institutions_list'))


# ============================================
# Institution Configuration
# ============================================

@institution_bp.route('/config', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin')
def config():
    """View and edit institution configuration."""
    # Root users should manage institutions from the institutions list, not this config page
    if current_user.is_root():
        return redirect(url_for('institution.institutions_list'))
    
    institution = get_current_institution()

    if request.method == 'POST':
        if not institution:
            flash('No hay institución configurada. Contacte al administrador del sistema.', 'error')
            return redirect(url_for('dashboard.index'))

        institution.name = request.form.get('name', '').strip()
        institution.nit = request.form.get('nit', '').strip()
        institution.address = request.form.get('address', '').strip()
        institution.phone = request.form.get('phone', '').strip()
        institution.email = request.form.get('email', '').strip()
        institution.municipality = request.form.get('municipality', '').strip()
        institution.department = request.form.get('department', '').strip()
        institution.resolution = request.form.get('resolution', '').strip()
        institution.academic_year = request.form.get('academic_year', '').strip()

        # Handle logo upload
        if 'logo' in request.files:
            logo = request.files['logo']
            if logo and logo.filename != '':
                # TODO: Implement logo upload logic
                pass

        try:
            db.session.commit()
            flash('Configuración de institución actualizada exitosamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'error')
        
        return redirect(url_for('institution.config'))
    
    return render_template('institution/config.html', institution=institution)


# ============================================
# Campuses CRUD
# ============================================

@institution_bp.route('/campuses')
@login_required
@role_required('root', 'admin', 'coordinator')
def campuses():
    """List all campuses."""
    # For root users, check if they want to change institution FIRST
    if current_user.is_root():
        change_institution = request.args.get('change_institution', type=int)
        if change_institution and 'active_institution_id' in session:
            del session['active_institution_id']
            flash('Institución deseleccionada. Selecciona una nueva.', 'info')
    
    # Now get current institution
    institution = get_current_institution()

    # For root users without active institution, show inline selector
    if not institution and current_user.is_root():
        institutions = Institution.query.order_by(Institution.name).all()
        return render_template('institution/campuses.html', 
                             campuses=[], 
                             institution=None,
                             institutions=institutions,
                             show_selector=True)

    if institution:
        campus_list = Campus.query.filter_by(institution_id=institution.id).order_by(Campus.name).all()
    else:
        # Root with institution selected can see all campuses
        campus_list = Campus.query.order_by(Campus.name).all()

    return render_template('institution/campuses.html', 
                         campuses=campus_list, 
                         institution=institution,
                         show_selector=False)


@institution_bp.route('/campuses/new', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin')
def campus_new():
    """Create a new campus."""
    institution = get_current_institution()

    # For root users without active institution
    if not institution and current_user.is_root():
        if request.method == 'POST':
            inst_id = request.form.get('institution_id', type=int)
            if inst_id:
                institution = Institution.query.get(inst_id)
                session['active_institution_id'] = institution.id
        
        if not institution:
            institutions = Institution.query.order_by(Institution.name).all()
            return render_template('institution/campus_form.html', 
                                 campus=None, 
                                 institution=None, 
                                 institutions=institutions,
                                 is_main_options=[])

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip()
        address = request.form.get('address', '').strip()
        jornada = request.form.get('jornada', 'completa')
        is_main = request.form.get('is_main_campus') == 'on'
        active = request.form.get('active') == 'on'
        
        errors = {}
        
        # Validate name
        if not name:
            errors['name'] = 'El nombre de la sede es obligatorio. Ejemplo: Sede Principal, Sede Norte'
        elif len(name) < 3:
            errors['name'] = 'El nombre debe tener al menos 3 caracteres'
        
        # Validate unique code within institution
        if code:
            existing_code = Campus.query.filter_by(
                institution_id=institution.id,
                code=code
            ).first()
            
            if existing_code:
                errors['code'] = f'Ya existe una sede con el código "{code}". Cada sede debe tener un código único. Sede existente: "{existing_code.name}"'
        
        # Validate only one main campus per institution
        if is_main:
            existing_main = Campus.query.filter_by(
                institution_id=institution.id,
                is_main_campus=True
            ).first()

            if existing_main:
                errors['is_main_campus'] = f'Ya existe una sede principal: "{existing_main.name}". Solo puede haber una sede principal por institución. Desmarca esa opción o edita la sede principal primero.'
        
        # If has errors, return form with data and errors
        if errors:
            institutions_list = Institution.query.order_by(Institution.name).all() if current_user.is_root() else [institution]
            flash('⚠️ Por favor corrige los errores marcados en el formulario', 'error')
            return render_template('institution/campus_form.html',
                                 campus=None,
                                 institution=institution,
                                 institutions=institutions_list,
                                 is_main_options=[],
                                 form_data={
                                     'name': name,
                                     'code': code,
                                     'address': address,
                                     'jornada': jornada,
                                     'is_main_campus': is_main,
                                     'active': active
                                 },
                                 errors=errors)

        campus = Campus(
            institution_id=institution.id,
            name=name,
            code=code if code else None,
            address=address if address else None,
            jornada=jornada,
            is_main_campus=is_main,
            active=active
        )

        try:
            db.session.add(campus)
            db.session.commit()
            flash('✅ Sede creada exitosamente.', 'success')
            return redirect(url_for('institution.campuses'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error al crear la sede: {str(e)}', 'error')
            institutions_list = Institution.query.order_by(Institution.name).all() if current_user.is_root() else [institution]
            return render_template('institution/campus_form.html',
                                 campus=None,
                                 institution=institution,
                                 institutions=institutions_list,
                                 is_main_options=[],
                                 form_data={
                                     'name': name,
                                     'code': code,
                                     'address': address,
                                     'jornada': jornada,
                                     'is_main_campus': is_main,
                                     'active': active
                                 },
                                 errors={'general': f'Error inesperado: {str(e)}'})

    # GET request - show form
    institutions_list = Institution.query.order_by(Institution.name).all() if current_user.is_root() else [institution]
    return render_template('institution/campus_form.html', 
                         campus=None, 
                         institution=institution, 
                         institutions=institutions_list,
                         is_main_options=[])


@institution_bp.route('/campuses/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin')
def campus_edit(id):
    """Edit an existing campus."""
    campus = db.session.get(Campus, id)

    if not campus:
        flash('Sede no encontrada.', 'error')
        return redirect(url_for('institution.campuses'))

    institution = get_current_institution()

    # Verify campus belongs to user's institution
    if institution and campus.institution_id != institution.id:
        flash('No tiene permiso para editar esta sede.', 'error')
        return redirect(url_for('institution.campuses'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip()
        address = request.form.get('address', '').strip()
        jornada = request.form.get('jornada', 'completa')
        is_main = request.form.get('is_main_campus') == 'on'
        active = request.form.get('active') == 'on'
        
        errors = {}
        
        # Validate name
        if not name:
            errors['name'] = 'El nombre de la sede es obligatorio. Ejemplo: Sede Principal, Sede Norte'
        elif len(name) < 3:
            errors['name'] = 'El nombre debe tener al menos 3 caracteres'
        
        # Validate unique code within institution (exclude current campus)
        if code and code != campus.code:
            existing_code = Campus.query.filter_by(
                institution_id=campus.institution_id,
                code=code
            ).first()
            
            if existing_code:
                errors['code'] = f'Ya existe una sede con el código "{code}". Cada sede debe tener un código único. Sede existente: "{existing_code.name}"'
        
        # Validate only one main campus per institution
        if is_main and not campus.is_main_campus:
            existing_main = Campus.query.filter_by(
                institution_id=campus.institution_id,
                is_main_campus=True
            ).first()

            if existing_main:
                errors['is_main_campus'] = f'Ya existe una sede principal: "{existing_main.name}". Solo puede haber una sede principal por institución. Desmarca esa opción o edita la sede principal primero.'
        
        # If has errors, return form with data and errors
        if errors:
            flash('⚠️ Por favor corrige los errores marcados en el formulario', 'error')
            return render_template('institution/campus_form.html',
                                 campus=campus,
                                 institution=institution,
                                 form_data={
                                     'name': name,
                                     'code': code,
                                     'address': address,
                                     'jornada': jornada,
                                     'is_main_campus': is_main,
                                     'active': active
                                 },
                                 errors=errors)

        campus.name = name
        campus.code = code if code else None
        campus.address = address if address else None
        campus.jornada = jornada
        campus.is_main_campus = is_main
        campus.active = active

        try:
            db.session.commit()
            flash('✅ Sede actualizada exitosamente.', 'success')
            return redirect(url_for('institution.campuses'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error al actualizar: {str(e)}', 'error')

    return render_template('institution/campus_form.html', campus=campus, institution=institution)


@institution_bp.route('/campuses/<int:id>/delete', methods=['POST'])
@login_required
@role_required('root', 'admin')
def campus_delete(id):
    """Delete a campus."""
    campus = db.session.get(Campus, id)
    
    if not campus:
        flash('Sede no encontrada.', 'error')
        return redirect(url_for('institution.campuses'))
    
    if campus.grades.count() > 0:
        flash('No se puede eliminar la sede porque tiene grados asignados.', 'warning')
        return redirect(url_for('institution.campuses'))
    
    try:
        db.session.delete(campus)
        db.session.commit()
        flash('Sede eliminada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {str(e)}', 'error')
    
    return redirect(url_for('institution.campuses'))


# ============================================
# Grades CRUD
# ============================================

@institution_bp.route('/grades')
@login_required
@role_required('root', 'admin', 'coordinator')
def grades():
    """List all grades."""
    # For root users, check if they want to change institution FIRST
    if current_user.is_root():
        change_institution = request.args.get('change_institution', type=int)
        if change_institution and 'active_institution_id' in session:
            del session['active_institution_id']
            flash('Institución deseleccionada. Selecciona una nueva.', 'info')
    
    # Now get current institution
    institution = get_current_institution()

    # For root users without active institution, show selector
    if not institution and current_user.is_root():
        institutions = Institution.query.order_by(Institution.name).all()
        return render_template('institution/grades.html', 
                             grades=[], 
                             institution=None,
                             institutions=institutions,
                             show_selector=True)

    if institution:
        grade_list = Grade.query.join(Campus).filter(
            Campus.institution_id == institution.id
        ).order_by(Grade.name).all()
    else:
        grade_list = Grade.query.order_by(Grade.name).all()

    return render_template('institution/grades.html', 
                         grades=grade_list, 
                         institution=institution,
                         show_selector=False)


@institution_bp.route('/grades/new', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin')
def grade_new():
    """Create a new grade."""
    institution = get_current_institution()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        campus_id = request.form.get('campus_id', type=int)
        director_id = request.form.get('director_id')
        academic_year = request.form.get('academic_year', '2026').strip()
        max_students = request.form.get('max_students', 40, type=int)
        
        errors = {}
        
        # Validate name
        if not name:
            errors['name'] = 'El nombre del grado es obligatorio. Ejemplo: 6-1, 11°B, Transición A'
        elif len(name) < 2:
            errors['name'] = 'El nombre debe tener al menos 2 caracteres'
        
        # Validate campus
        if not campus_id:
            errors['campus_id'] = 'Debes seleccionar una sede donde funcionará este grado'
        
        # If has errors, return form with data
        if errors:
            flash('⚠️ Por favor corrige los errores marcados en el formulario', 'error')
            if institution:
                campuses = Campus.query.filter_by(institution_id=institution.id, active=True).order_by(Campus.name).all()
                teachers = User.query.filter_by(role='teacher', institution_id=institution.id).order_by(User.first_name).all()
            else:
                campuses = Campus.query.filter_by(active=True).order_by(Campus.name).all()
                teachers = User.query.filter_by(role='teacher').order_by(User.first_name).all()
            
            return render_template('institution/grade_form.html',
                                 grade=None,
                                 campuses=campuses,
                                 teachers=teachers,
                                 institution=institution,
                                 form_data={
                                     'name': name,
                                     'campus_id': campus_id,
                                     'director_id': director_id,
                                     'academic_year': academic_year,
                                     'max_students': max_students
                                 },
                                 errors=errors)
        
        campus = db.session.get(Campus, campus_id)

        # Verify campus belongs to user's institution
        if institution and campus.institution_id != institution.id:
            flash('❌ No tiene permiso para crear grados en esta sede.', 'error')
            return redirect(url_for('institution.grades'))

        grade = Grade(
            campus_id=campus.id,
            director_id=int(director_id) if director_id else None,
            name=name,
            academic_year=academic_year,
            max_students=max_students
        )

        try:
            db.session.add(grade)
            db.session.commit()
            flash('✅ Grado creado exitosamente.', 'success')
            return redirect(url_for('institution.grades'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error al crear el grado: {str(e)}', 'error')
            if institution:
                campuses = Campus.query.filter_by(institution_id=institution.id, active=True).order_by(Campus.name).all()
                teachers = User.query.filter_by(role='teacher', institution_id=institution.id).order_by(User.first_name).all()
            else:
                campuses = Campus.query.filter_by(active=True).order_by(Campus.name).all()
                teachers = User.query.filter_by(role='teacher').order_by(User.first_name).all()
            
            return render_template('institution/grade_form.html',
                                 grade=None,
                                 campuses=campuses,
                                 teachers=teachers,
                                 institution=institution,
                                 form_data={
                                     'name': name,
                                     'campus_id': campus_id,
                                     'director_id': director_id,
                                     'academic_year': academic_year,
                                     'max_students': max_students
                                 },
                                 errors={'general': f'Error inesperado: {str(e)}'})

    if institution:
        campuses = Campus.query.filter_by(institution_id=institution.id, active=True).order_by(Campus.name).all()
        # Get teachers from this institution
        teachers = User.query.filter_by(role='teacher', institution_id=institution.id).order_by(User.first_name).all()
    else:
        campuses = Campus.query.filter_by(active=True).order_by(Campus.name).all()
        teachers = User.query.filter_by(role='teacher').order_by(User.first_name).all()

    return render_template('institution/grade_form.html', grade=None, campuses=campuses, teachers=teachers, institution=institution)


@institution_bp.route('/grades/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin')
def grade_edit(id):
    """Edit an existing grade."""
    grade = db.session.get(Grade, id)

    if not grade:
        flash('Grado no encontrado.', 'error')
        return redirect(url_for('institution.grades'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        campus_id = request.form.get('campus_id', type=int)
        director_id = request.form.get('director_id')
        academic_year = request.form.get('academic_year', '2026').strip()
        max_students = request.form.get('max_students', 40, type=int)

        errors = {}
        if not name:
            errors['name'] = 'El nombre del grado es obligatorio'
        if not campus_id:
            errors['campus_id'] = 'Debes seleccionar una sede'

        if errors:
            flash('⚠️ Por favor corrige los errores marcados en el formulario', 'error')
            campuses = Campus.query.filter_by(active=True).order_by(Campus.name).all()
            teachers = User.query.filter_by(role='teacher').order_by(User.first_name).all()
            return render_template('institution/grade_form.html',
                                 grade=grade,
                                 campuses=campuses,
                                 teachers=teachers,
                                 form_data={
                                     'name': name,
                                     'campus_id': campus_id,
                                     'director_id': director_id,
                                     'academic_year': academic_year,
                                     'max_students': max_students
                                 },
                                 errors=errors)

        grade.campus_id = campus_id
        grade.director_id = int(director_id) if director_id else None
        grade.name = name
        grade.academic_year = academic_year
        grade.max_students = max_students

        try:
            db.session.commit()
            flash('✅ Grado actualizado exitosamente.', 'success')
            return redirect(url_for('institution.grades'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error al actualizar: {str(e)}', 'error')
            campuses = Campus.query.filter_by(active=True).order_by(Campus.name).all()
            teachers = User.query.filter_by(role='teacher').order_by(User.first_name).all()
            return render_template('institution/grade_form.html',
                                 grade=grade,
                                 campuses=campuses,
                                 teachers=teachers,
                                 form_data={
                                     'name': name,
                                     'campus_id': campus_id,
                                     'director_id': director_id,
                                     'academic_year': academic_year,
                                     'max_students': max_students
                                 },
                                 errors={'general': f'Error inesperado: {str(e)}'})

    campuses = Campus.query.filter_by(active=True).order_by(Campus.name).all()
    teachers = User.query.filter_by(role='teacher').order_by(User.first_name).all()

    return render_template('institution/grade_form.html', grade=grade, campuses=campuses, teachers=teachers)


@institution_bp.route('/grades/<int:id>/delete', methods=['POST'])
@login_required
@role_required('root', 'admin')
def grade_delete(id):
    """Delete a grade."""
    grade = db.session.get(Grade, id)
    
    if not grade:
        flash('Grado no encontrado.', 'error')
        return redirect(url_for('institution.grades'))
    
    if grade.academic_students.count() > 0:
        flash('No se puede eliminar el grado porque tiene estudiantes asignados.', 'warning')
        return redirect(url_for('institution.grades'))
    
    try:
        db.session.delete(grade)
        db.session.commit()
        flash('Grado eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {str(e)}', 'error')
    
    return redirect(url_for('institution.grades'))


# ============================================
# Subjects CRUD
# ============================================

@institution_bp.route('/subjects')
@login_required
@role_required('root', 'admin', 'coordinator', 'teacher')
def subjects():
    """List all subjects."""
    institution = get_current_institution()
    
    if institution:
        subject_list = Subject.query.filter_by(institution_id=institution.id).order_by(Subject.name).all()
    else:
        subject_list = Subject.query.order_by(Subject.name).all()
    
    return render_template('institution/subjects.html', subjects=subject_list, institution=institution)


@institution_bp.route('/subjects/new', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin')
def subject_new():
    """Create a new subject."""
    institution = get_current_institution()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip()
        
        errors = {}
        if not name:
            errors['name'] = 'El nombre de la asignatura es obligatorio'
        
        if errors:
            flash('⚠️ Por favor corrige los errores marcados en el formulario', 'error')
            institutions = [institution] if institution else Institution.query.order_by(Institution.name).all()
            return render_template('institution/subject_form.html', 
                                 subject=None, 
                                 institutions=institutions,
                                 form_data={'name': name, 'code': code},
                                 errors=errors)

        if not institution:
            flash('Debe seleccionar una institución para crear la asignatura.', 'error')
            institutions = Institution.query.order_by(Institution.name).all()
            return render_template('institution/subject_form.html', subject=None, institutions=institutions)

        subject = Subject(
            institution_id=institution.id,
            name=name,
            code=code
        )

        try:
            db.session.add(subject)
            db.session.commit()
            flash('✅ Asignatura creada exitosamente.', 'success')
            return redirect(url_for('institution.subjects'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error al crear la asignatura: {str(e)}', 'error')
            institutions = [institution] if institution else Institution.query.order_by(Institution.name).all()
            return render_template('institution/subject_form.html', 
                                 subject=None, 
                                 institutions=institutions,
                                 form_data={'name': name, 'code': code},
                                 errors={'general': f'Error inesperado: {str(e)}'})

    institution = get_current_institution()
    institutions = [institution] if institution else Institution.query.order_by(Institution.name).all()
    return render_template('institution/subject_form.html', subject=None, institutions=institutions)


@institution_bp.route('/subjects/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin')
def subject_edit(id):
    """Edit an existing subject."""
    subject = db.session.get(Subject, id)

    if not subject:
        flash('Asignatura no encontrada.', 'error')
        return redirect(url_for('institution.subjects'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip()
        
        errors = {}
        if not name:
            errors['name'] = 'El nombre de la asignatura es obligatorio'
        
        if errors:
            flash('⚠️ Por favor corrige los errores marcados en el formulario', 'error')
            return render_template('institution/subject_form.html', 
                                 subject=subject,
                                 form_data={'name': name, 'code': code},
                                 errors=errors)

        subject.name = name
        subject.code = code

        try:
            db.session.commit()
            flash('✅ Asignatura actualizada exitosamente.', 'success')
            return redirect(url_for('institution.subjects'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error al actualizar: {str(e)}', 'error')
            return render_template('institution/subject_form.html', 
                                 subject=subject,
                                 form_data={'name': name, 'code': code},
                                 errors={'general': f'Error inesperado: {str(e)}'})

    return render_template('institution/subject_form.html', subject=subject)


@institution_bp.route('/subjects/<int:id>/delete', methods=['POST'])
@login_required
@role_required('root', 'admin')
def subject_delete(id):
    """Delete a subject."""
    subject = db.session.get(Subject, id)
    
    if not subject:
        flash('Asignatura no encontrada.', 'error')
        return redirect(url_for('institution.subjects'))
    
    if subject.subject_grades.count() > 0:
        flash('No se puede eliminar la asignatura porque tiene grados asignados.', 'warning')
        return redirect(url_for('institution.subjects'))
    
    try:
        db.session.delete(subject)
        db.session.commit()
        flash('Asignatura eliminada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {str(e)}', 'error')
    
    return redirect(url_for('institution.subjects'))


# ============================================
# Academic Periods CRUD
# ============================================

@institution_bp.route('/periods')
@login_required
@role_required('root', 'admin', 'coordinator')
def periods():
    """List all academic periods."""
    institution = get_current_institution()
    
    if institution:
        period_list = AcademicPeriod.query.filter_by(institution_id=institution.id).order_by(AcademicPeriod.order).all()
    else:
        period_list = AcademicPeriod.query.order_by(AcademicPeriod.order).all()
    
    return render_template('institution/periods.html', periods=period_list, institution=institution)


@institution_bp.route('/periods/new', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin')
def period_new():
    """Create a new academic period."""
    institution = get_current_institution()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        short_name = request.form.get('short_name', '').strip()
        start_date = request.form.get('start_date', '').strip()
        end_date = request.form.get('end_date', '').strip()
        academic_year = request.form.get('academic_year', '2026').strip()
        order = request.form.get('order', '1').strip()
        is_active = request.form.get('is_active') == 'on'
        
        errors = {}
        if not name:
            errors['name'] = 'El nombre del periodo es obligatorio'
        if not short_name:
            errors['short_name'] = 'El nombre corto es obligatorio'
        if not start_date:
            errors['start_date'] = 'La fecha de inicio es obligatoria'
        if not end_date:
            errors['end_date'] = 'La fecha de fin es obligatoria'
        
        if errors:
            flash('⚠️ Por favor corrige los errores marcados en el formulario', 'error')
            institutions = [institution] if institution else Institution.query.order_by(Institution.name).all()
            return render_template('institution/period_form.html', 
                                 period=None, 
                                 institutions=institutions,
                                 form_data={
                                     'name': name,
                                     'short_name': short_name,
                                     'start_date': start_date,
                                     'end_date': end_date,
                                     'academic_year': academic_year,
                                     'order': order,
                                     'is_active': is_active
                                 },
                                 errors=errors)

        if not institution:
            institution_id = request.form.get('institution_id')
            if institution_id:
                institution = Institution.query.get(int(institution_id))
            else:
                flash('Debe seleccionar una institución para crear el periodo.', 'error')
                institutions = Institution.query.order_by(Institution.name).all()
                return render_template('institution/period_form.html', period=None, institutions=institutions)

        from datetime import datetime
        period = AcademicPeriod(
            institution_id=institution.id,
            name=name,
            short_name=short_name,
            start_date=datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None,
            end_date=datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None,
            is_active=is_active,
            academic_year=academic_year,
            order=int(order) if order else 1
        )

        try:
            db.session.add(period)
            db.session.commit()
            flash('✅ Periodo académico creado exitosamente.', 'success')
            return redirect(url_for('institution.periods'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error al crear el periodo: {str(e)}', 'error')
            institutions = [institution] if institution else Institution.query.order_by(Institution.name).all()
            return render_template('institution/period_form.html', 
                                 period=None, 
                                 institutions=institutions,
                                 form_data={
                                     'name': name,
                                     'short_name': short_name,
                                     'start_date': start_date,
                                     'end_date': end_date,
                                     'academic_year': academic_year,
                                     'order': order,
                                     'is_active': is_active
                                 },
                                 errors={'general': f'Error inesperado: {str(e)}'})

    institution = get_current_institution()
    institutions = [institution] if institution else Institution.query.order_by(Institution.name).all()
    return render_template('institution/period_form.html', period=None, institutions=institutions)


@institution_bp.route('/periods/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin')
def period_edit(id):
    """Edit an academic period."""
    period = db.session.get(AcademicPeriod, id)

    if not period:
        flash('Periodo no encontrado.', 'error')
        return redirect(url_for('institution.periods'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        short_name = request.form.get('short_name', '').strip()
        start_date = request.form.get('start_date', '').strip()
        end_date = request.form.get('end_date', '').strip()
        academic_year = request.form.get('academic_year', '2026').strip()
        order = request.form.get('order', '1').strip()
        is_active = request.form.get('is_active') == 'on'
        
        errors = {}
        if not name:
            errors['name'] = 'El nombre del periodo es obligatorio'
        if not short_name:
            errors['short_name'] = 'El nombre corto es obligatorio'
        if not start_date:
            errors['start_date'] = 'La fecha de inicio es obligatoria'
        if not end_date:
            errors['end_date'] = 'La fecha de fin es obligatoria'
        
        if errors:
            flash('⚠️ Por favor corrige los errores marcados en el formulario', 'error')
            from datetime import datetime
            return render_template('institution/period_form.html', 
                                 period=period,
                                 form_data={
                                     'name': name,
                                     'short_name': short_name,
                                     'start_date': start_date,
                                     'end_date': end_date,
                                     'academic_year': academic_year,
                                     'order': order,
                                     'is_active': is_active
                                 },
                                 errors=errors)

        from datetime import datetime
        period.name = name
        period.short_name = short_name
        period.start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else period.start_date
        period.end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else period.end_date
        period.is_active = is_active
        period.academic_year = academic_year
        period.order = int(order) if order else period.order

        try:
            db.session.commit()
            flash('✅ Periodo académico actualizado exitosamente.', 'success')
            return redirect(url_for('institution.periods'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error al actualizar: {str(e)}', 'error')
            return render_template('institution/period_form.html', 
                                 period=period,
                                 form_data={
                                     'name': name,
                                     'short_name': short_name,
                                     'start_date': start_date,
                                     'end_date': end_date,
                                     'academic_year': academic_year,
                                     'order': order,
                                     'is_active': is_active
                                 },
                                 errors={'general': f'Error inesperado: {str(e)}'})

    return render_template('institution/period_form.html', period=period)


@institution_bp.route('/periods/<int:id>/delete', methods=['POST'])
@login_required
@role_required('root', 'admin')
def period_delete(id):
    """Delete an academic period."""
    period = db.session.get(AcademicPeriod, id)
    
    if not period:
        flash('Periodo no encontrado.', 'error')
        return redirect(url_for('institution.periods'))
    
    if period.grade_records.count() > 0:
        flash('No se puede eliminar el periodo porque tiene registros de notas.', 'warning')
        return redirect(url_for('institution.periods'))
    
    try:
        db.session.delete(period)
        db.session.commit()
        flash('Periodo académico eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {str(e)}', 'error')
    
    return redirect(url_for('institution.periods'))


# ============================================
# Evaluation Criteria CRUD
# ============================================

@institution_bp.route('/criteria')
@login_required
@role_required('root', 'admin', 'coordinator', 'teacher')
def criteria():
    """List all evaluation criteria."""
    institution = get_current_institution()
    
    if institution:
        criteria_list = GradeCriteria.query.filter_by(institution_id=institution.id).order_by(GradeCriteria.order).all()
    else:
        criteria_list = GradeCriteria.query.order_by(GradeCriteria.order).all()
    
    return render_template('institution/criteria.html', criteria=criteria_list, institution=institution)


@institution_bp.route('/criteria/new', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin')
def criteria_new():
    """Create a new evaluation criterion."""
    institution = get_current_institution()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        weight = request.form.get('weight', '').strip()
        description = request.form.get('description', '').strip()
        order = request.form.get('order', '1').strip()

        errors = {}
        if not name:
            errors['name'] = 'El nombre del criterio es obligatorio'
        if not weight:
            errors['weight'] = 'El peso es obligatorio'
        else:
            try:
                weight_val = float(weight)
                if weight_val <= 0 or weight_val > 100:
                    errors['weight'] = 'El peso debe ser mayor a 0 y menor o igual a 100'
            except ValueError:
                errors['weight'] = 'El peso debe ser un número válido'

        if errors:
            flash('⚠️ Por favor corrige los errores marcados en el formulario', 'error')
            institutions = [institution] if institution else Institution.query.order_by(Institution.name).all()
            return render_template('institution/criteria_form.html',
                                 criterion=None,
                                 institutions=institutions,
                                 form_data={
                                     'name': name,
                                     'weight': weight,
                                     'description': description,
                                     'order': order
                                 },
                                 errors=errors)

        if not institution:
            institution_id = request.form.get('institution_id')
            if institution_id:
                institution = Institution.query.get(int(institution_id))
            else:
                flash('Debe seleccionar una institución para crear el criterio.', 'error')
                institutions = Institution.query.order_by(Institution.name).all()
                return render_template('institution/criteria_form.html', criterion=None, institutions=institutions)

        criterion = GradeCriteria(
            institution_id=institution.id,
            name=name,
            weight=float(weight),
            description=description,
            order=int(order) if order else 1
        )

        try:
            db.session.add(criterion)
            db.session.commit()
            flash('✅ Criterio de evaluación creado exitosamente.', 'success')
            return redirect(url_for('institution.criteria'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error al crear el criterio: {str(e)}', 'error')
            institutions = [institution] if institution else Institution.query.order_by(Institution.name).all()
            return render_template('institution/criteria_form.html',
                                 criterion=None,
                                 institutions=institutions,
                                 form_data={
                                     'name': name,
                                     'weight': weight,
                                     'description': description,
                                     'order': order
                                 },
                                 errors={'general': f'Error inesperado: {str(e)}'})

    institution = get_current_institution()
    institutions = [institution] if institution else Institution.query.order_by(Institution.name).all()
    return render_template('institution/criteria_form.html', criterion=None, institutions=institutions)


@institution_bp.route('/criteria/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin')
def criteria_edit(id):
    """Edit an evaluation criterion."""
    criterion = db.session.get(GradeCriteria, id)

    if not criterion:
        flash('Criterio no encontrado.', 'error')
        return redirect(url_for('institution.criteria'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        weight = request.form.get('weight', '').strip()
        description = request.form.get('description', '').strip()
        order = request.form.get('order', '1').strip()

        errors = {}
        if not name:
            errors['name'] = 'El nombre del criterio es obligatorio'
        if not weight:
            errors['weight'] = 'El peso es obligatorio'
        else:
            try:
                weight_val = float(weight)
                if weight_val <= 0 or weight_val > 100:
                    errors['weight'] = 'El peso debe ser mayor a 0 y menor o igual a 100'
            except ValueError:
                errors['weight'] = 'El peso debe ser un número válido'

        if errors:
            flash('⚠️ Por favor corrige los errores marcados en el formulario', 'error')
            return render_template('institution/criteria_form.html',
                                 criterion=criterion,
                                 form_data={
                                     'name': name,
                                     'weight': weight,
                                     'description': description,
                                     'order': order
                                 },
                                 errors=errors)

        criterion.name = name
        criterion.weight = float(weight)
        criterion.description = description
        criterion.order = int(order) if order else criterion.order

        try:
            db.session.commit()
            flash('✅ Criterio de evaluación actualizado exitosamente.', 'success')
            return redirect(url_for('institution.criteria'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error al actualizar: {str(e)}', 'error')
            return render_template('institution/criteria_form.html',
                                 criterion=criterion,
                                 form_data={
                                     'name': name,
                                     'weight': weight,
                                     'description': description,
                                     'order': order
                                 },
                                 errors={'general': f'Error inesperado: {str(e)}'})

    return render_template('institution/criteria_form.html', criterion=criterion)


@institution_bp.route('/criteria/<int:id>/delete', methods=['POST'])
@login_required
@role_required('root', 'admin')
def criteria_delete(id):
    """Delete an evaluation criterion."""
    criterion = db.session.get(GradeCriteria, id)
    
    if not criterion:
        flash('Criterio no encontrado.', 'error')
        return redirect(url_for('institution.criteria'))
    
    if criterion.grade_records.count() > 0:
        flash('No se puede eliminar el criterio porque tiene registros de notas.', 'warning')
        return redirect(url_for('institution.criteria'))
    
    try:
        db.session.delete(criterion)
        db.session.commit()
        flash('Criterio de evaluación eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {str(e)}', 'error')

    return redirect(url_for('institution.criteria'))


# ============================================
# Institution Switching (Root Users)
# ============================================

@institution_bp.route('/switch', methods=['POST'])
@login_required
@role_required('root')
def switch_institution():
    """Switch active institution for root users."""
    from flask import session
    
    institution_id = request.form.get('institution_id')

    if not institution_id:
        # Clear active institution - root sees all
        if 'active_institution_id' in session:
            del session['active_institution_id']
        flash('Ahora puede ver todas las instituciones.', 'info')
        next_url = request.form.get('next', url_for('institution.institutions_list'))
        return redirect(next_url)

    institution = Institution.query.get(int(institution_id))

    if not institution:
        flash('Institución no encontrada.', 'error')
        next_url = request.form.get('next', url_for('institution.institutions_list'))
        return redirect(next_url)

    session['active_institution_id'] = institution.id
    flash(f'✅ Institución seleccionada: {institution.name}', 'success')

    # Redirect to specified next URL
    next_url = request.form.get('next', url_for('dashboard.index'))
    return redirect(next_url)


@institution_bp.route('/select-institution/<int:id>')
@login_required
@role_required('root')
def select_and_manage_institution(id):
    """Select a specific institution and redirect to campus management."""
    from flask import session
    
    institution = Institution.query.get(id)
    if not institution:
        flash('Institución no encontrada.', 'error')
        return redirect(url_for('institution.institutions_list'))
    
    # Set active institution
    session['active_institution_id'] = institution.id
    flash(f'🏫 Trabajando en: {institution.name}', 'info')
    
    # Redirect to campus management
    return redirect(url_for('institution.campuses'))


@institution_bp.route('/institutions/select')
@login_required
@role_required('root')
def select_institution():
    """Show institution selection page for root users."""
    all_institutions = Institution.query.order_by(Institution.name).all()
    return render_template('institution/select_institution.html', institutions=all_institutions)


# ============================================
# Root: Institution User Management
# ============================================

@institution_bp.route('/<int:id>/users')
@login_required
@role_required('root')
def institution_users(id):
    """View all users of a specific institution - root only."""
    institution = db.session.get(Institution, id)
    if not institution:
        flash('Institución no encontrada.', 'error')
        return redirect(url_for('institution.institutions_list'))
    
    users = User.query.filter_by(institution_id=id).order_by(User.role, User.first_name).all()
    
    stats = {
        'total': len(users),
        'admin': sum(1 for u in users if u.role == 'admin'),
        'coordinator': sum(1 for u in users if u.role == 'coordinator'),
        'teacher': sum(1 for u in users if u.role == 'teacher'),
        'student': sum(1 for u in users if u.role == 'student'),
    }
    
    return render_template(
        'institution/institution_users.html',
        institution=institution,
        users=users,
        stats=stats
    )


@institution_bp.route('/<int:id>/users/add-admin', methods=['GET', 'POST'])
@login_required
@role_required('root')
def institution_add_admin(id):
    """Add a new admin to an institution - root only."""
    institution = db.session.get(Institution, id)
    if not institution:
        flash('Institución no encontrada.', 'error')
        return redirect(url_for('institution.institutions_list'))

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        document_type = request.form.get('document_type', 'CC')
        document_number = request.form.get('document_number', '').strip()
        phone = request.form.get('phone', '').strip() or None
        role = request.form.get('role', 'teacher').strip()

        errors = {}

        # Validate required fields
        if not first_name:
            errors['first_name'] = 'El nombre es obligatorio'
        if not last_name:
            errors['last_name'] = 'El apellido es obligatorio'
        if not email:
            errors['email'] = 'El email es obligatorio'
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors['email'] = 'El email no tiene un formato válido'
        if not document_number:
            errors['document_number'] = 'El número de documento es obligatorio'
        elif len(document_number) < 5:
            errors['document_number'] = 'El documento debe tener al menos 5 caracteres'
        if not role:
            errors['role'] = 'El rol es obligatorio'

        # Check email uniqueness
        if email and User.query.filter_by(email=email).first():
            errors['email'] = 'El email ya está registrado en el sistema'

        # Check document number uniqueness
        if document_number and User.query.filter_by(document_number=document_number).first():
            errors['document_number'] = f'El documento "{document_number}" ya está registrado. Cada usuario debe tener un documento único.'

        # If has errors, return form with data and errors
        if errors:
            flash('⚠️ Por favor corrige los errores marcados en el formulario', 'error')
            return render_template('institution/add_admin_form.html',
                                 institution=institution,
                                 form_data={
                                     'first_name': first_name,
                                     'last_name': last_name,
                                     'email': email,
                                     'document_type': document_type,
                                     'document_number': document_number,
                                     'phone': phone,
                                     'role': role
                                 },
                                 errors=errors)

        from werkzeug.security import generate_password_hash
        from utils.username_generator import generate_username, generate_username_from_db

        username = generate_username_from_db(
            first_name,
            last_name,
            query_func=lambda pattern: [
                u.username for u in User.query.filter(
                    User.username.like(f'{pattern}%')
                ).all()
            ]
        )

        # La contraseña es el número de documento
        default_password = document_number.strip()

        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(default_password),
            first_name=first_name,
            last_name=last_name,
            role=role,
            institution_id=institution.id,
            document_type=document_type,
            document_number=document_number,
            phone=phone,
            country='Colombia',
            is_active=True,
            must_change_password=True
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            
            role_names = {
                'admin': 'Administrador',
                'coordinator': 'Coordinador',
                'teacher': 'Profesor',
                'student': 'Estudiante',
                'parent': 'Acudiente',
                'viewer': 'Viewer'
            }
            role_display = role_names.get(role, role.title())
            
            flash(f'✅ {role_display} "{username}" creado exitosamente para {institution.name}.', 'success')
            return redirect(url_for('institution.institution_users', id=id))
        except Exception as e:
            db.session.rollback()
            
            # Handle duplicate document/email gracefully
            error_str = str(e).lower()
            if 'unique' in error_str and 'document_number' in error_str:
                errors['document_number'] = f'El documento "{document_number}" ya está registrado.'
            elif 'unique' in error_str and 'email' in error_str:
                errors['email'] = 'El email ya está registrado en el sistema.'
            
            if errors:
                flash('⚠️ Por favor corrige los errores marcados en el formulario', 'error')
                return render_template('institution/add_admin_form.html',
                                     institution=institution,
                                     form_data={
                                         'first_name': first_name,
                                         'last_name': last_name,
                                         'email': email,
                                         'document_type': document_type,
                                         'document_number': document_number,
                                         'phone': phone,
                                         'role': role
                                     },
                                     errors=errors)
            
            flash(f'❌ Error al crear: {str(e)}', 'error')
            return render_template('institution/add_admin_form.html',
                                 institution=institution,
                                 form_data={
                                     'first_name': first_name,
                                     'last_name': last_name,
                                     'email': email,
                                     'document_type': document_type,
                                     'document_number': document_number,
                                     'phone': phone,
                                     'role': role
                                 },
                                 errors={'general': f'Error inesperado: {str(e)}'})

    return render_template('institution/add_admin_form.html', institution=institution)


@institution_bp.route('/users/<int:user_id>/change-password', methods=['POST'])
@login_required
@role_required('root')
def change_user_password(user_id):
    """Change any user's password - root only."""
    user = db.session.get(User, user_id)
    if not user:
        flash('Usuario no encontrado.', 'error')
        return redirect(url_for('institution.institutions_list'))

    new_password = request.form.get('new_password', '').strip()
    if not new_password or len(new_password) < 6:
        flash('La contraseña debe tener al menos 6 caracteres.', 'error')
        return redirect(url_for('users.user_edit', id=user_id))

    from werkzeug.security import generate_password_hash
    user.password_hash = generate_password_hash(new_password)
    user.must_change_password = True

    try:
        db.session.commit()
        flash(f'✅ Contraseña de {user.username} actualizada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar: {str(e)}', 'error')

    # Redirect back to institution users page
    return redirect(url_for('institution.institution_users', id=user.institution_id))


# ============================================
# API Routes for Campus Management (AJAX)
# ============================================

@institution_bp.route('/api/campuses/<int:institution_id>', methods=['GET'])
@login_required
@role_required('root', 'admin')
def api_get_campuses(institution_id):
    """API endpoint to get all campuses for an institution."""
    institution = Institution.query.get(institution_id)
    
    if not institution:
        return {'error': 'Institución no encontrada'}, 404
    
    # Verify permission
    if not current_user.is_root() and current_user.institution_id != institution_id:
        return {'error': 'No tienes permiso para ver esta institución'}, 403
    
    campuses = Campus.query.filter_by(institution_id=institution_id).order_by(Campus.is_main_campus.desc(), Campus.name).all()
    
    # Build campus data
    campus_data = []
    for campus in campuses:
        campus_data.append({
            'id': campus.id,
            'name': campus.name,
            'code': campus.code,
            'address': campus.address,
            'jornada': campus.jornada,
            'is_main_campus': campus.is_main_campus,
            'active': campus.active,
            'grades_count': campus.grades.count(),
            'created_at': campus.to_dict().get('created_at')
        })
    
    # Calculate stats
    main_campus = Campus.query.filter_by(institution_id=institution_id, is_main_campus=True).first()
    
    stats = {
        'total': len(campuses),
        'active': sum(1 for c in campuses if c.active),
        'inactive': sum(1 for c in campuses if not c.active),
        'main_name': main_campus.name if main_campus else None
    }
    
    return {
        'campuses': campus_data,
        'stats': stats
    }


@institution_bp.route('/api/campuses/<int:institution_id>/<int:campus_id>', methods=['GET'])
@login_required
@role_required('root', 'admin')
def api_get_campus(institution_id, campus_id):
    """API endpoint to get a single campus."""
    campus = Campus.query.get(campus_id)
    
    if not campus or campus.institution_id != institution_id:
        return {'error': 'Sede no encontrada'}, 404
    
    # Verify permission
    if not current_user.is_root() and current_user.institution_id != institution_id:
        return {'error': 'No tienes permiso'}, 403
    
    return campus.to_dict()


@institution_bp.route('/api/campuses/<int:institution_id>', methods=['POST'])
@login_required
@role_required('root', 'admin')
def api_create_campus(institution_id):
    """API endpoint to create a new campus."""
    institution = Institution.query.get(institution_id)
    
    if not institution:
        return {'error': 'Institución no encontrada'}, 404
    
    # Verify permission
    if not current_user.is_root() and current_user.institution_id != institution_id:
        return {'error': 'No tienes permiso'}, 403
    
    data = request.get_json()
    
    name = data.get('name', '').strip()
    if not name:
        return {'error': 'El nombre de la sede es obligatorio'}, 400
    
    code = data.get('code', '').strip()
    address = data.get('address', '').strip()
    jornada = data.get('jornada', 'completa')
    active = data.get('active', True)
    is_main_campus = data.get('is_main_campus', False)
    
    # Validate only one main campus
    if is_main_campus:
        existing_main = Campus.query.filter_by(institution_id=institution_id, is_main_campus=True).first()
        if existing_main:
            return {'error': f'Ya existe una sede principal: {existing_main.name}'}, 400
    
    campus = Campus(
        institution_id=institution_id,
        name=name,
        code=code if code else None,
        address=address if address else None,
        jornada=jornada,
        is_main_campus=is_main_campus,
        active=active
    )
    
    try:
        db.session.add(campus)
        db.session.commit()
        return {
            'message': 'Sede creada exitosamente',
            'id': campus.id
        }, 201
    except Exception as e:
        db.session.rollback()
        return {'error': f'Error al crear la sede: {str(e)}'}, 500


@institution_bp.route('/api/campuses/<int:institution_id>/<int:campus_id>', methods=['PUT'])
@login_required
@role_required('root', 'admin')
def api_update_campus(institution_id, campus_id):
    """API endpoint to update a campus."""
    campus = Campus.query.get(campus_id)
    
    if not campus or campus.institution_id != institution_id:
        return {'error': 'Sede no encontrada'}, 404
    
    # Verify permission
    if not current_user.is_root() and current_user.institution_id != institution_id:
        return {'error': 'No tienes permiso'}, 403
    
    data = request.get_json()
    
    name = data.get('name', '').strip()
    if not name:
        return {'error': 'El nombre de la sede es obligatorio'}, 400
    
    # Validate only one main campus
    is_main_campus = data.get('is_main_campus', False)
    if is_main_campus and not campus.is_main_campus:
        existing_main = Campus.query.filter_by(institution_id=institution_id, is_main_campus=True).first()
        if existing_main:
            return {'error': f'Ya existe una sede principal: {existing_main.name}'}, 400
    
    campus.name = name
    campus.code = data.get('code', '').strip() if data.get('code') else None
    campus.address = data.get('address', '').strip() if data.get('address') else None
    campus.jornada = data.get('jornada', campus.jornada)
    campus.active = data.get('active', campus.active)
    campus.is_main_campus = is_main_campus
    
    try:
        db.session.commit()
        return {'message': 'Sede actualizada exitosamente'}
    except Exception as e:
        db.session.rollback()
        return {'error': f'Error al actualizar: {str(e)}'}, 500


@institution_bp.route('/api/campuses/<int:institution_id>/<int:campus_id>', methods=['DELETE'])
@login_required
@role_required('root', 'admin')
def api_delete_campus(institution_id, campus_id):
    """API endpoint to delete a campus."""
    campus = Campus.query.get(campus_id)
    
    if not campus or campus.institution_id != institution_id:
        return {'error': 'Sede no encontrada'}, 404
    
    # Verify permission
    if not current_user.is_root() and current_user.institution_id != institution_id:
        return {'error': 'No tienes permiso'}, 403
    
    # Check for related grades
    if campus.grades.count() > 0:
        return {'error': 'No se puede eliminar la sede porque tiene grados asociados'}, 400
    
    try:
        db.session.delete(campus)
        db.session.commit()
        return {'message': 'Sede eliminada exitosamente'}
    except Exception as e:
        db.session.rollback()
        return {'error': f'Error al eliminar: {str(e)}'}, 500
