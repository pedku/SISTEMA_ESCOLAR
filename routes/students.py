"""
Student management routes.
Full CRUD for students, Excel upload, profile management, guardian data.
"""

import os
import pandas as pd
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, session
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from extensions import db
from models.user import User
from models.institution import Institution, Campus
from models.academic import Grade, AcademicStudent, ParentStudent, SubjectGrade
from models.scheduling import Schedule
from utils.decorators import role_required
from utils.validators import validate_document, validate_email
from utils.institution_resolver import get_current_institution, get_institution_students
from utils.username_generator import generate_username_from_db

students_bp = Blueprint('students', __name__)


# ============================================
# Student List
# ============================================

@students_bp.route('/')
@login_required
@role_required('root', 'admin', 'coordinator', 'teacher')
def list():
    """List all students with filters. Includes students without academic profile."""
    institution = get_current_institution()

    # Get filters
    campus_id = request.args.get('campus_id', type=int)
    grade_id = request.args.get('grade_id', type=int)
    status = request.args.get('status', 'activo')
    search = request.args.get('search', '')

    # Build query using institution-aware helper
    query = get_institution_students(institution)

    if campus_id:
        query = query.filter_by(campus_id=campus_id)
    if grade_id:
        query = query.filter_by(grade_id=grade_id)
    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.join(User).filter(
            db.or_(
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%'),
                User.document_number.ilike(f'%{search}%')
            )
        )

    students = query.join(User).order_by(User.last_name).all()

    # Also find users with role=student who don't have academic profile yet
    # This helps admins identify incomplete student registrations
    student_users_query = User.query.filter_by(role='student', is_active=True)

    # Filter by institution
    if institution:
        student_users_query = student_users_query.filter(
            db.or_(
                User.institution_id == institution.id,
                User.institution_id.is_(None)  # Include students without institution set
            )
        )

    if search:
        student_users_query = student_users_query.filter(
            db.or_(
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%'),
                User.document_number.ilike(f'%{search}%')
            )
        )

    all_student_users = student_users_query.order_by(User.last_name).all()

    # Find which ones don't have academic profile
    academic_user_ids = set(s.user_id for s in students)
    incomplete_profiles = [u for u in all_student_users if u.id not in academic_user_ids]

    # Filter campuses by institution
    if institution:
        campuses = Campus.query.filter_by(active=True, institution_id=institution.id).all()
        grades = Grade.query.join(Campus).filter(Campus.institution_id == institution.id).all()
    else:
        # Root without active institution: see all
        campuses = Campus.query.filter_by(active=True).all()
        grades = Grade.query.all()

    return render_template('students/list.html',
                          students=students,
                          incomplete_profiles=incomplete_profiles,
                          campuses=campuses,
                          grades=grades,
                          selected_campus=campus_id,
                          selected_grade=grade_id,
                          selected_status=status,
                          search=search)


# ============================================
# Student Profile
# ============================================

@students_bp.route('/<int:id>')
@login_required
@role_required('root', 'admin', 'coordinator', 'teacher')
def profile(id):
    """View student profile including their class schedule."""
    try:
        student = db.session.get(AcademicStudent, id)
        
        if not student:
            flash('Estudiante no encontrado.', 'error')
            return redirect(url_for('students.list'))
        
        # Load schedule if student has a grade assigned
        schedule_grid = {}
        days = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes']
        schedules = []
        
        if student.grade_id:
            institution = get_current_institution()
            academic_year = institution.academic_year if institution else '2026'
            
            schedules = Schedule.query.join(SubjectGrade).filter(
                SubjectGrade.grade_id == student.grade_id,
                Schedule.academic_year == academic_year,
                Schedule.is_active == True
            ).order_by(Schedule.day_of_week, Schedule.start_time).all()
            
            # Organize into grid
            for sch in schedules:
                day_idx = sch.day_of_week
                time_key = sch.start_time.strftime('%H:%M')
                
                if day_idx not in schedule_grid:
                    schedule_grid[day_idx] = {}
                
                schedule_grid[day_idx][time_key] = sch

        return render_template('students/profile.html', 
                              student=student, 
                              schedules=schedules,
                              schedule_grid=schedule_grid,
                              days=days)
    except Exception as e:
        import traceback
        return f"<h1>Error de Servidor</h1><pre>{traceback.format_exc()}</pre>", 500


# ============================================
# Create Student
# ============================================

@students_bp.route('/new', methods=['GET', 'POST'])
@students_bp.route('/new/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def new(user_id=None):
    """Create a new student. If user_id is provided, only ask for academic info."""
    institution = get_current_institution()
    existing_user = None
    
    # If user_id is provided, load the existing user
    if user_id:
        existing_user = User.query.get(user_id)
        if not existing_user or existing_user.role != 'student':
            flash('Usuario no encontrado o no es un estudiante.', 'error')
            return redirect(url_for('users.users_list'))

    # For root users, allow switching institution via URL parameter
    if current_user.is_root() and not existing_user:
        # Check if user wants to change institution
        change_institution = request.args.get('change_institution', type=int)
        if change_institution:
            # Clear current institution and show selector
            if 'active_institution_id' in session:
                del session['active_institution_id']
            institution = None

        # If still no institution, show selector or handle selection
        if not institution:
            # Check for institution_id in both POST form and GET query params
            inst_id = None
            if request.method == 'POST':
                inst_id = request.form.get('institution_id', type=int)
            else:
                inst_id = request.args.get('institution_id', type=int)

            if inst_id:
                institution = Institution.query.get(inst_id)
                # Set in session for future requests
                session['active_institution_id'] = institution.id

            if not institution:
                # Show form with institution selector for root
                institutions = Institution.query.order_by(Institution.name).all()
                return render_template('students/form.html', student=None, institution=None, institutions=institutions, campuses=[], grades=[], existing_user=None)
    elif not institution and not existing_user:
        # For admin/coordinator without institution assigned
        flash('Debe seleccionar una institución antes de crear estudiantes.', 'error')
        return redirect(url_for('institution.select_institution'))

    if request.method == 'POST':
        # If existing_user is provided, only create academic student record
        if existing_user:
            from services.student_service import StudentService
            enrolled_year = (institution or existing_user.institution).academic_year if (institution or existing_user.institution) else '2026'
            inst_id = institution.id if institution else existing_user.institution_id
            
            result = StudentService.create_academic_profile(existing_user, request.form, inst_id, enrolled_year)
            
            if result['success']:
                flash(f"✅ Perfil académico creado exitosamente para {existing_user.get_full_name()}.", 'success')
                return redirect(url_for('students.list'))
            else:
                flash(f"❌ Error al crear perfil académico: {result['error']}", 'error')
                campus_id = request.form.get('campus_id', type=int)
                campuses = Campus.query.filter_by(institution_id=inst_id, active=True).order_by(Campus.name).all()
                grades = Grade.query.filter_by(campus_id=campus_id).order_by(Grade.name).all() if campus_id else []
                return render_template('students/form.html', student=None, institution=institution or existing_user.institution, campuses=campuses, grades=grades, existing_user=existing_user)
        
        from services.student_service import StudentService
        result = StudentService.create_student(request.form, institution.id, institution.academic_year)
        
        if result['success']:
            flash(f"Estudiante creado exitosamente. Usuario: {result['username']}, Contraseña: estudiante123", 'success')
            return redirect(url_for('students.profile', id=result['student'].id))
        else:
            flash(f"Error al crear el estudiante: {result['error']}", 'error')
    
    # Determine which institution to use
    current_inst = institution or (existing_user.institution if existing_user else None)
    
    if current_inst:
        campuses = Campus.query.filter_by(active=True, institution_id=current_inst.id).all()
        grades = Grade.query.join(Campus).filter(Campus.institution_id == current_inst.id).all()
    else:
        campuses = []
        grades = []

    return render_template('students/form.html', student=None, campuses=campuses, grades=grades, institution=current_inst, existing_user=existing_user)


# ============================================
# Edit Student
# ============================================

@students_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def edit(id):
    """Edit an existing student."""
    student = db.session.get(AcademicStudent, id)

    if not student:
        flash('Estudiante no encontrado.', 'error')
        return redirect(url_for('students.list'))

    institution = get_current_institution()

    if not institution:
        flash('Debe seleccionar una institución antes de editar estudiantes.', 'error')
        return redirect(url_for('students.list'))

    if request.method == 'POST':
        # Update User (Identity and Location)
        user = db.session.get(User, student.user_id)
        user.first_name = request.form.get('first_name', '').strip()
        user.last_name = request.form.get('last_name', '').strip()
        user.phone = request.form.get('phone', '').strip()
        user.address = request.form.get('address', '').strip()
        user.birth_date = datetime.strptime(request.form.get('birth_date'), '%Y-%m-%d').date() if request.form.get('birth_date') else None
        user.gender = request.form.get('gender', '')

        # Update AcademicStudent (Academic and Well-being)
        student.campus_id = int(request.form.get('campus_id'))
        student.grade_id = int(request.form.get('grade_id')) if request.form.get('grade_id') else None
        student.neighborhood = request.form.get('neighborhood', '').strip()
        student.stratum = int(request.form.get('stratum')) if request.form.get('stratum') else None
        student.blood_type = request.form.get('blood_type', '').strip()
        student.eps = request.form.get('eps', '').strip()
        student.guardian_name = request.form.get('guardian_name', '').strip()
        student.guardian_phone = request.form.get('guardian_phone', '').strip()
        student.guardian_email = request.form.get('guardian_email', '').strip()
        student.status = request.form.get('status', 'activo')

        try:
            db.session.commit()
            flash('✅ Perfil del estudiante actualizado exitosamente.', 'success')
            return redirect(url_for('students.profile', id=student.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'error')

    campuses = Campus.query.filter_by(active=True, institution_id=institution.id).all()
    grades = Grade.query.join(Campus).filter(Campus.institution_id == institution.id).all()

    return render_template('students/form.html', student=student, campuses=campuses, grades=grades, institution=institution)


# ============================================
# Delete Student
# ============================================

@students_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def delete(id):
    """Delete a student and all associated records."""
    student = db.session.get(AcademicStudent, id)

    if not student:
        flash('Estudiante no encontrado.', 'error')
        return redirect(url_for('students.list'))

    try:
        # Import models that reference AcademicStudent (avoid circular imports)
        from models.alert import Alert
        from models.observation import Observation
        from models.attendance import Attendance
        from models.achievement import StudentAchievement
        from models.grading import GradeRecord, FinalGrade, AnnualGrade
        from models.report import ReportCard
        from models.academic import ParentStudent

        # Delete all associated records that reference this student
        Alert.query.filter_by(student_id=student.id).delete()
        Observation.query.filter_by(student_id=student.id).delete()
        Attendance.query.filter_by(student_id=student.id).delete()
        StudentAchievement.query.filter_by(student_id=student.id).delete()
        GradeRecord.query.filter_by(student_id=student.id).delete()
        FinalGrade.query.filter_by(student_id=student.id).delete()
        AnnualGrade.query.filter_by(student_id=student.id).delete()
        ReportCard.query.filter_by(student_id=student.id).delete()
        ParentStudent.query.filter_by(student_id=student.id).delete()

        # Delete the student
        db.session.delete(student)

        # Delete associated user
        user = db.session.get(User, student.user_id)
        if user:
            db.session.delete(user)

        db.session.commit()
        flash('Estudiante eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {str(e)}', 'error')

    return redirect(url_for('students.list'))


# ============================================
# Excel Upload
# ============================================

@students_bp.route('/upload', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def upload():
    """Upload students from Excel file."""
    institution = get_current_institution()

    # For root users without active institution, show institution selector
    if not institution and current_user.is_root():
        # Check for institution_id in query params (GET) or form (POST)
        inst_id = None
        if request.method == 'POST':
            inst_id = request.form.get('institution_id', type=int)
        else:
            inst_id = request.args.get('institution_id', type=int)

        if inst_id:
            institution = Institution.query.get(inst_id)
            if institution:
                session['active_institution_id'] = institution.id
            else:
                flash('Institucion no encontrada.', 'error')
                return redirect(url_for('students.list'))

        if not institution:
            # Show form with institution selector for root
            institutions = Institution.query.order_by(Institution.name).all()
            return render_template('students/upload.html', institutions=institutions)

    if not institution:
        flash('Debe seleccionar una institucion antes de importar estudiantes.', 'error')
        return redirect(url_for('students.list'))

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No se seleccionó ningún archivo.', 'warning')
        file = request.files['file']

        if file.filename == '':
            flash('No se seleccionó ningún archivo.', 'warning')
            return render_template('students/upload.html')

        if not file.filename.endswith(('.xlsx', '.xls')):
            flash('Solo se permiten archivos Excel (.xlsx, .xls).', 'error')
            return render_template('students/upload.html')

        # Save file temporarily
        upload_folder = current_app.config['UPLOAD_FOLDER']
        excel_folder = os.path.join(upload_folder, 'excel_imports')
        os.makedirs(excel_folder, exist_ok=True)

        file_path = os.path.join(excel_folder, file.filename)
        file.save(file_path)

        from services.excel_handler import ExcelHandlerService
        result = ExcelHandlerService.process_student_upload(file_path, institution)
        
        if result['success']:
            if result.get('created_count', 0) > 0:
                flash(f"{result['created_count']} estudiantes importados exitosamente.", 'success')
            
            if result.get('errors'):
                flash(f"{len(result['errors'])} errores encontrados. Revisa el archivo de errores.", 'warning')
                # Save errors to file
                error_file = os.path.join(excel_folder, f'errores_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
                with open(error_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(result['errors']))
            return redirect(url_for('students.list'))
        else:
            flash(f"Error al procesar el archivo: {result.get('error', 'Desconocido')}", 'error')

    return render_template('students/upload.html')


# ============================================
# Asignar Acudientes
# ============================================

@students_bp.route('/<int:id>/assign-parent', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def assign_parent(id):
    """Asignar acudientes a un estudiante"""
    student = db.session.get(AcademicStudent, id)
    
    if not student:
        flash('Estudiante no encontrado.', 'error')
        return redirect(url_for('students.list'))
    
    institution = get_current_institution()
    
    if request.method == 'POST':
        parent_id = request.form.get('parent_id', type=int)
        relationship = request.form.get('relationship', '').strip()
        
        if not parent_id:
            flash('Debes seleccionar un acudiente.', 'error')
            return redirect(url_for('students.assign_parent', id=id))
        
        # Verificar que el usuario es acudiente
        parent = db.session.get(User, parent_id)
        if not parent or parent.role != 'parent':
            flash('El usuario seleccionado no es un acudiente.', 'error')
            return redirect(url_for('students.assign_parent', id=id))
        
        # Verificar que no esté ya asignado
        existing = ParentStudent.query.filter_by(parent_id=parent_id, student_id=student.id).first()
        if existing:
            flash('Este acudiente ya está asignado al estudiante.', 'warning')
            return redirect(url_for('students.assign_parent', id=id))
        
        # Crear la relación
        ps = ParentStudent(
            parent_id=parent_id,
            student_id=student.id,
            relationship=relationship or 'Acudiente'
        )
        
        try:
            db.session.add(ps)
            db.session.commit()
            flash('✅ Acudiente asignado exitosamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error al asignar acudiente: {str(e)}', 'error')
        
        return redirect(url_for('students.assign_parent', id=id))
    
    # Obtener acudientes disponibles
    parents = User.query.filter_by(role='parent', institution_id=institution.id, is_active=True).order_by(User.last_name).all()
    
    # Obtener acudientes ya asignados
    assigned_parents = ParentStudent.query.filter_by(student_id=student.id).all()
    
    return render_template('students/assign_parent.html', 
                          student=student, 
                          parents=parents, 
                          assigned_parents=assigned_parents)


@students_bp.route('/<int:id>/remove-parent/<int:parent_id>', methods=['POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def remove_parent(id, parent_id):
    """Eliminar asignación de acudiente"""
    ps = ParentStudent.query.filter_by(student_id=id, parent_id=parent_id).first()
    
    if not ps:
        flash('Asignación no encontrada.', 'error')
    else:
        try:
            db.session.delete(ps)
            db.session.commit()
            flash('✅ Acudiente eliminado exitosamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error al eliminar: {str(e)}', 'error')
    
    return redirect(url_for('students.assign_parent', id=id))
