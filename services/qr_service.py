import uuid
import hashlib
from datetime import datetime, time
import pytz
from extensions import db
from models.qr_access import QRToken, QRAccessLog
from models.user import User
from models.scheduling import Classroom, Schedule, TeacherSubjectAssignment, StudentEnrollment

COLOMBIA_TZ = pytz.timezone('America/Bogota')

class QRService:
    @staticmethod
    def get_or_create_token(user_id):
        """
        Retrieves the active token for a user or creates a new one if it doesn't exist.
        """
        token_entry = QRToken.query.filter_by(user_id=user_id, is_active=True).first()
        if not token_entry:
            # Generate a unique token (UUID based)
            new_token_str = str(uuid.uuid4())
            token_entry = QRToken(user_id=user_id, token=new_token_str)
            db.session.add(token_entry)
            db.session.commit()
        return token_entry

    @staticmethod
    def regenerate_token(user_id):
        """
        Invalidates existing tokens and generates a new one.
        """
        QRToken.query.filter_by(user_id=user_id).update({'is_active': False})
        new_token_str = str(uuid.uuid4())
        token_entry = QRToken(user_id=user_id, token=new_token_str)
        db.session.add(token_entry)
        db.session.commit()
        return token_entry

    @staticmethod
    def validate_access(token_str, classroom_name_or_code, ip_address=None):
        """
        Validates access based on token, classroom, and current schedule.
        Returns (bool, message, user_obj)
        """
        now = datetime.now(COLOMBIA_TZ)
        current_time = now.time()
        current_day = now.weekday()  # 0=Monday
        
        # 1. Identity Validation
        token_entry = QRToken.query.filter_by(token=token_str, is_active=True).first()
        if not token_entry:
            log = QRAccessLog(status='invalid_token', message='Token no válido o inactivo', ip_address=ip_address)
            db.session.add(log)
            db.session.commit()
            return False, "Token inválido o inactivo", None

        user = token_entry.user
        
        # 2. Classroom Validation
        classroom = Classroom.query.filter(
            (Classroom.name == classroom_name_or_code) | (Classroom.code == classroom_name_or_code)
        ).first()
        
        if not classroom:
            log = QRAccessLog(user_id=user.id, status='denied', 
                             message=f'Salón no encontrado: {classroom_name_or_code}', 
                             ip_address=ip_address)
            db.session.add(log)
            db.session.commit()
            return False, "Ubicación no reconocida", user

        # 3. Schedule Validation
        # Check if there's a schedule for this classroom and time
        # We need to consider both students and teachers
        
        valid_schedule = False
        
        # Get all active schedules for this classroom today
        schedules = Schedule.query.filter_by(
            classroom_id=classroom.id,
            day_of_week=current_day,
            is_active=True
        ).all()
        
        # Check if current time falls within any schedule
        matching_schedule = None
        for s in schedules:
            if s.start_time <= current_time <= s.end_time:
                matching_schedule = s
                break
        
        if not matching_schedule:
            # Maybe it's a bit early? (Allow 10 mins early)
            # This is a refinement
            pass
            
        if matching_schedule:
            # Now verify if the user belongs to this subject_grade
            subject_grade_id = matching_schedule.subject_grade_id
            
            if user.role == 'teacher':
                # Check if this teacher is assigned to this subject_grade
                assignment = TeacherSubjectAssignment.query.filter_by(
                    subject_grade_id=subject_grade_id,
                    teacher_id=user.id,
                    status='activo'
                ).first()
                if assignment:
                    valid_schedule = True
            
            elif user.role == 'student':
                # Check if this student is enrolled in this subject_grade
                # Note: user.id maps to User, but enrollment uses AcademicStudent.id
                # User has academic_profile backref
                if hasattr(user, 'academic_profile') and user.academic_profile:
                    enrollment = StudentEnrollment.query.filter_by(
                        subject_grade_id=subject_grade_id,
                        student_id=user.academic_profile.id,
                        status='activa'
                    ).first()
                    if enrollment:
                        valid_schedule = True
            
            elif user.role in ['root', 'admin', 'coordinator']:
                # Admins can enter anywhere
                valid_schedule = True

        if valid_schedule:
            status = 'authorized'
            msg = f"Acceso concedido a {user.name}"
            # Update token usage
            token_entry.last_used_at = now
        else:
            status = 'wrong_schedule'
            msg = "No tiene clase programada en este horario/salón"

        # Log attempt
        log = QRAccessLog(
            user_id=user.id,
            classroom_id=classroom.id,
            timestamp=now,
            status=status,
            message=msg,
            ip_address=ip_address
        )
        db.session.add(log)
        db.session.commit()
        
        return valid_schedule, msg, user
