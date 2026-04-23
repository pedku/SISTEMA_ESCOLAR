"""
Student service.
Handles creation and management of student profiles and parent assignments.
"""

from extensions import db
from models.user import User
from models.academic import AcademicStudent, ParentStudent
from utils.username_generator import generate_username_from_db
from werkzeug.security import generate_password_hash
from utils.validators import validate_document, validate_email
from datetime import datetime

class StudentService:

    @staticmethod
    def create_student(form_data, institution_id, enrolled_year):
        """Create a new user and academic student profile."""
        doc_type = form_data.get('document_type', 'TI')
        doc_number = form_data.get('document_number', '').strip()
        
        is_valid, error_msg = validate_document(doc_type, doc_number)
        if not is_valid:
            return {'success': False, 'error': error_msg}
        
        # Check existing
        if User.query.filter_by(document_number=doc_number).first():
            return {'success': False, 'error': 'Ya existe un usuario con ese número de documento.'}
        
        if AcademicStudent.query.filter_by(document_number=doc_number).first():
            return {'success': False, 'error': 'Ya existe un estudiante con ese número de documento.'}
        
        first_name = form_data.get('first_name', '').strip()
        last_name = form_data.get('last_name', '').strip()

        if not first_name or not last_name:
            return {'success': False, 'error': 'Nombre y apellido son requeridos.'}

        username = generate_username_from_db(
            first_name, 
            last_name,
            query_func=lambda pattern: [
                u.username for u in User.query.filter(User.username.like(f'{pattern}%')).all()
            ]
        )
        
        email = form_data.get('email', '').strip()
        if not email:
            email = f"{username}@sige.edu.co"
        else:
            if not validate_email(email):
                return {'success': False, 'error': 'El correo electrónico no es válido.'}
        
        if User.query.filter_by(email=email).first():
            return {'success': False, 'error': 'El correo electrónico ya está en uso.'}
        
        try:
            # Create User
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash('estudiante123'),
                first_name=first_name,
                last_name=last_name,
                document_type=doc_type,
                document_number=doc_number,
                phone=form_data.get('phone', '').strip(),
                address=form_data.get('address', '').strip(),
                role='student',
                institution_id=institution_id,
                is_active=True
            )
            db.session.add(user)
            db.session.flush()
            
            grade_id = form_data.get('grade_id')
            
            # Create AcademicStudent
            student = AcademicStudent(
                user_id=user.id,
                institution_id=institution_id,
                campus_id=int(form_data.get('campus_id')),
                grade_id=int(grade_id) if grade_id else None,
                document_type=doc_type,
                document_number=doc_number,
                birth_date=datetime.strptime(form_data.get('birth_date'), '%Y-%m-%d').date() if form_data.get('birth_date') else None,
                address=form_data.get('student_address', '').strip(),
                neighborhood=form_data.get('neighborhood', '').strip(),
                stratum=int(form_data.get('stratum')) if form_data.get('stratum') else None,
                gender=form_data.get('gender', ''),
                blood_type=form_data.get('blood_type', '').strip(),
                eps=form_data.get('eps', '').strip(),
                guardian_name=form_data.get('guardian_name', '').strip(),
                guardian_phone=form_data.get('guardian_phone', '').strip(),
                guardian_email=form_data.get('guardian_email', '').strip(),
                enrolled_year=enrolled_year,
                status='activo'
            )
            db.session.add(student)
            db.session.commit()
            
            return {'success': True, 'student': student, 'username': username}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def create_academic_profile(existing_user, form_data, institution_id, enrolled_year):
        """Create academic profile for an existing user."""
        campus_id = form_data.get('campus_id')
        if not campus_id:
            return {'success': False, 'error': 'Debes seleccionar una sede.'}
            
        grade_id = form_data.get('grade_id')
        
        student = AcademicStudent(
            user_id=existing_user.id,
            institution_id=institution_id,
            campus_id=int(campus_id),
            grade_id=int(grade_id) if grade_id else None,
            document_type=existing_user.document_type,
            document_number=existing_user.document_number,
            birth_date=datetime.strptime(form_data.get('birth_date'), '%Y-%m-%d').date() if form_data.get('birth_date') else None,
            address=form_data.get('student_address', '').strip(),
            neighborhood=form_data.get('neighborhood', '').strip(),
            stratum=int(form_data.get('stratum')) if form_data.get('stratum') else None,
            gender=form_data.get('gender', ''),
            blood_type=form_data.get('blood_type', '').strip(),
            eps=form_data.get('eps', '').strip(),
            guardian_name=form_data.get('guardian_name', '').strip(),
            guardian_phone=form_data.get('guardian_phone', '').strip(),
            guardian_email=form_data.get('guardian_email', '').strip(),
            enrolled_year=enrolled_year,
            status='activo'
        )
        
        try:
            db.session.add(student)
            db.session.commit()
            return {'success': True, 'student': student}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
