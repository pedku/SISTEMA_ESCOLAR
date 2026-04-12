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
from models.academic import Grade, AcademicStudent, ParentStudent
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
    """List all students with filters."""
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
    """View student profile."""
    student = db.session.get(AcademicStudent, id)
    
    if not student:
        flash('Estudiante no encontrado.', 'error')
        return redirect(url_for('students.list'))
    
    return render_template('students/profile.html', student=student)


# ============================================
# Create Student
# ============================================

@students_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def new():
    """Create a new student."""
    institution = get_current_institution()

    # For root users, allow switching institution via URL parameter
    if current_user.is_root():
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
                return render_template('students/form.html', student=None, institution=None, institutions=institutions, campuses=[], grades=[])
    elif not institution:
        # For admin/coordinator without institution assigned
        flash('Debe seleccionar una institución antes de crear estudiantes.', 'error')
        return redirect(url_for('institution.select_institution'))

    if request.method == 'POST':
        # Validate document
        doc_type = request.form.get('document_type', 'TI')
        doc_number = request.form.get('document_number', '').strip()
        
        is_valid, error_msg = validate_document(doc_type, doc_number)
        if not is_valid:
            flash(error_msg, 'error')
            return render_template('students/form.html', student=None, institution=institution)
        
        # Check if document already exists
        existing_user = User.query.filter_by(document_number=doc_number).first()
        if existing_user:
            flash('Ya existe un usuario con ese número de documento.', 'error')
            return render_template('students/form.html', student=None, institution=institution)
        
        existing_student = AcademicStudent.query.filter_by(document_number=doc_number).first()
        if existing_student:
            flash('Ya existe un estudiante con ese número de documento.', 'error')
            return render_template('students/form.html', student=None, institution=institution)
        
        # Generate username using new dynamic system
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()

        if not first_name or not last_name:
            flash('Nombre y apellido son requeridos.', 'error')
            return render_template('students/form.html', student=None, institution=institution)

        # Generate username with incremental numbering (pcastro1, pcastro2, etc.)
        username = generate_username_from_db(
            first_name, 
            last_name,
            query_func=lambda pattern: [
                u.username for u in User.query.filter(
                    User.username.like(f'{pattern}%')
                ).all()
            ]
        )
        
        # Create email
        email = request.form.get('email', '').strip()
        if not email:
            email = f"{username}@sige.edu.co"
        else:
            is_valid_email = validate_email(email)
            if not is_valid_email:
                flash('El correo electrónico no es válido.', 'error')
                return render_template('students/form.html', student=None, institution=institution)
        
        # Check if email exists
        if User.query.filter_by(email=email).first():
            flash('El correo electrónico ya está en uso.', 'error')
            return render_template('students/form.html', student=None, institution=institution)
        
        # Create User
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash('estudiante123'),  # Default password
            first_name=first_name,
            last_name=last_name,
            document_type=doc_type,
            document_number=doc_number,
            phone=request.form.get('phone', '').strip(),
            address=request.form.get('address', '').strip(),
            role='student',
            is_active=True
        )
        db.session.add(user)
        db.session.flush()  # Get user ID without committing
        
        # Create AcademicStudent
        student = AcademicStudent(
            user_id=user.id,
            institution_id=institution.id,
            campus_id=int(request.form.get('campus_id')),
            grade_id=int(request.form.get('grade_id')) if request.form.get('grade_id') else None,
            document_type=doc_type,
            document_number=doc_number,
            birth_date=datetime.strptime(request.form.get('birth_date'), '%Y-%m-%d').date() if request.form.get('birth_date') else None,
            address=request.form.get('student_address', '').strip(),
            neighborhood=request.form.get('neighborhood', '').strip(),
            stratum=int(request.form.get('stratum')) if request.form.get('stratum') else None,
            gender=request.form.get('gender', ''),
            blood_type=request.form.get('blood_type', '').strip(),
            eps=request.form.get('eps', '').strip(),
            guardian_name=request.form.get('guardian_name', '').strip(),
            guardian_phone=request.form.get('guardian_phone', '').strip(),
            guardian_email=request.form.get('guardian_email', '').strip(),
            enrolled_year=institution.academic_year,
            status='activo'
        )
        db.session.add(student)
        
        try:
            db.session.commit()
            flash(f'Estudiante creado exitosamente. Usuario: {username}, Contraseña: estudiante123', 'success')
            return redirect(url_for('students.profile', id=student.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el estudiante: {str(e)}', 'error')
    
    campuses = Campus.query.filter_by(active=True, institution_id=institution.id).all()
    grades = Grade.query.join(Campus).filter(Campus.institution_id == institution.id).all()

    return render_template('students/form.html', student=None, campuses=campuses, grades=grades, institution=institution)


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
        # Update User
        user = db.session.get(User, student.user_id)
        user.first_name = request.form.get('first_name', '').strip()
        user.last_name = request.form.get('last_name', '').strip()
        user.phone = request.form.get('phone', '').strip()
        user.address = request.form.get('address', '').strip()

        # Update AcademicStudent
        student.campus_id = int(request.form.get('campus_id'))
        student.grade_id = int(request.form.get('grade_id')) if request.form.get('grade_id') else None
        student.birth_date = datetime.strptime(request.form.get('birth_date'), '%Y-%m-%d').date() if request.form.get('birth_date') else None
        student.address = request.form.get('student_address', '').strip()
        student.neighborhood = request.form.get('neighborhood', '').strip()
        student.stratum = int(request.form.get('stratum')) if request.form.get('stratum') else None
        student.gender = request.form.get('gender', '')
        student.blood_type = request.form.get('blood_type', '').strip()
        student.eps = request.form.get('eps', '').strip()
        student.guardian_name = request.form.get('guardian_name', '').strip()
        student.guardian_phone = request.form.get('guardian_phone', '').strip()
        student.guardian_email = request.form.get('guardian_email', '').strip()
        student.status = request.form.get('status', 'activo')

        try:
            db.session.commit()
            flash('Estudiante actualizado exitosamente.', 'success')
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
    """Delete a student."""
    student = db.session.get(AcademicStudent, id)
    
    if not student:
        flash('Estudiante no encontrado.', 'error')
        return redirect(url_for('students.list'))
    
    try:
        # Delete associated user
        user = db.session.get(User, student.user_id)
        db.session.delete(student)
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

    if not institution:
        flash('Debe seleccionar una institución antes de importar estudiantes.', 'error')
        return redirect(url_for('students.list'))

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No se seleccionó ningún archivo.', 'warning')
            return render_template('students/upload.html')

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

        try:
            # Read Excel file
            df = pd.read_excel(file_path)

            # Expected columns (flexible matching)
            col_mapping = {
                'nombre': 'first_name',
                'apellido': 'last_name',
                'documento': 'document_number',
                'tipo_documento': 'document_type',
                'fecha_nacimiento': 'birth_date',
                'genero': 'gender',
                'grado': 'grade_name',
                'sede': 'campus_name',
                'acudiente': 'guardian_name',
                'telefono_acudiente': 'guardian_phone',
                'email_acudiente': 'guardian_email',
                'direccion': 'address',
                'barrio': 'neighborhood',
                'estrato': 'stratum',
                'tipo_sangre': 'blood_type',
                'eps': 'eps'
            }

            # Normalize column names
            df.columns = [col.lower().strip().replace(' ', '_') for col in df.columns]

            created_count = 0
            errors = []

            for index, row in df.iterrows():
                try:
                    # Extract data
                    first_name = str(row.get('nombre', '')).strip()
                    last_name = str(row.get('apellido', '')).strip()
                    doc_number = str(row.get('documento', '')).strip()

                    if not first_name or not last_name or not doc_number:
                        errors.append(f"Fila {index + 2}: Nombre, apellido y documento son requeridos")
                        continue

                    # Check if student already exists
                    if AcademicStudent.query.filter_by(document_number=doc_number).first():
                        errors.append(f"Fila {index + 2}: Estudiante con documento {doc_number} ya existe")
                        continue

                    # Generate username with incremental numbering
                    username = generate_username_from_db(
                        first_name,
                        last_name,
                        query_func=lambda pattern: [
                            u.username for u in User.query.filter(
                                User.username.like(f'{pattern}%')
                            ).all()
                        ]
                    )

                    # Create user
                    user = User(
                        username=username,
                        email=f"{username}@sige.edu.co",
                        password_hash=generate_password_hash('estudiante123'),
                        first_name=first_name,
                        last_name=last_name,
                        document_type=str(row.get('tipo_documento', 'TI')).strip(),
                        document_number=doc_number,
                        role='student',
                        is_active=True
                    )
                    db.session.add(user)
                    db.session.flush()

                    # Find campus
                    campus_name = str(row.get('sede', '')).strip()
                    campus = Campus.query.filter_by(
                        name=campus_name,
                        institution_id=institution.id
                    ).first() if campus_name else Campus.query.filter_by(
                        institution_id=institution.id
                    ).first()

                    if not campus:
                        errors.append(f"Fila {index + 2}: Sede '{campus_name}' no encontrada")
                        db.session.rollback()
                        continue

                    # Find grade
                    grade_name = str(row.get('grado', '')).strip()
                    grade = Grade.query.filter_by(
                        name=grade_name,
                        campus_id=campus.id,
                    ).first() if grade_name else None

                    # Create academic student
                    student = AcademicStudent(
                        user_id=user.id,
                        institution_id=institution.id,
                        campus_id=campus.id,
                        grade_id=grade.id if grade else None,
                        document_type=str(row.get('tipo_documento', 'TI')).strip(),
                        document_number=doc_number,
                        birth_date=pd.to_datetime(row.get('fecha_nacimiento')).date() if pd.notna(row.get('fecha_nacimiento')) else None,
                        address=str(row.get('direccion', '')).strip(),
                        neighborhood=str(row.get('barrio', '')).strip(),
                        stratum=int(row.get('estrato')) if pd.notna(row.get('estrato')) else None,
                        gender=str(row.get('genero', '')).strip(),
                        blood_type=str(row.get('tipo_sangre', '')).strip(),
                        eps=str(row.get('eps', '')).strip(),
                        guardian_name=str(row.get('acudiente', '')).strip(),
                        guardian_phone=str(row.get('telefono_acudiente', '')).strip(),
                        guardian_email=str(row.get('email_acudiente', '')).strip(),
                        enrolled_year=institution.academic_year,
                        status='activo'
                    )
                    db.session.add(student)
                    created_count += 1

                except Exception as e:
                    errors.append(f"Fila {index + 2}: Error - {str(e)}")
                    db.session.rollback()

            db.session.commit()

            if created_count > 0:
                flash(f'{created_count} estudiantes importados exitosamente.', 'success')

            if errors:
                flash(f'{len(errors)} errores encontrados. Revisa el archivo de errores.', 'warning')
                # Save errors to file
                error_file = os.path.join(excel_folder, f'errores_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
                with open(error_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(errors))

            return redirect(url_for('students.list'))

        except Exception as e:
            flash(f'Error al procesar el archivo: {str(e)}', 'error')

    return render_template('students/upload.html')
