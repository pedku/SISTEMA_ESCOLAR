"""
Scheduling and Enrollment models.
Handles student enrollment, teacher assignments, classroom management, and schedules.
"""

from datetime import datetime
from extensions import db


class Classroom(db.Model):
    """Classroom/Room model (e.g., "Aula 101", "Lab Ciencias")."""

    __tablename__ = 'classrooms'

    id = db.Column(db.Integer, primary_key=True)
    campus_id = db.Column(db.Integer, db.ForeignKey('campuses.id'), nullable=False, index=True)
    name = db.Column(db.String(50), nullable=False)
    code = db.Column(db.String(20), index=True)
    capacity = db.Column(db.Integer, default=40)
    floor = db.Column(db.Integer, default=1)
    building = db.Column(db.String(50))
    classroom_type = db.Column(db.String(50), default='aula')  # aula, laboratorio, auditorio, cancha
    resources = db.Column(db.Text)  # JSON string of available resources

    # Relationships
    campus = db.relationship('Campus', backref='classrooms', lazy=True)
    schedules = db.relationship('Schedule', backref='classroom', lazy='dynamic', cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('campus_id', 'code', name='uq_classroom_campus_code'),
    )

    def __repr__(self):
        return f'<Classroom {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'campus_id': self.campus_id,
            'name': self.name,
            'code': self.code,
            'capacity': self.capacity,
            'floor': self.floor,
            'building': self.building,
            'classroom_type': self.classroom_type,
            'resources': self.resources
        }


class StudentEnrollment(db.Model):
    """Student enrollment in a SubjectGrade (matricula)."""

    __tablename__ = 'student_enrollments'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('academic_students.id'), nullable=False, index=True)
    subject_grade_id = db.Column(db.Integer, db.ForeignKey('subject_grades.id'), nullable=False, index=True)
    academic_year = db.Column(db.String(20), nullable=False, index=True)
    enrollment_date = db.Column(db.Date, default=datetime.utcnow)
    status = db.Column(db.String(20), default='activa', index=True)  # activa, cancelada, retirada
    final_score = db.Column(db.Float)
    status_note = db.Column(db.Text)

    # Relationships
    student = db.relationship('AcademicStudent', backref='enrollments', lazy=True)
    subject_grade = db.relationship('SubjectGrade', backref='enrollments', lazy=True)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'subject_grade_id', 'academic_year', name='uq_enrollment_student_subject_year'),
    )

    def __repr__(self):
        return f'<StudentEnrollment {self.student.user.username} - {self.subject_grade.subject.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'subject_grade_id': self.subject_grade_id,
            'academic_year': self.academic_year,
            'enrollment_date': self.enrollment_date.isoformat() if self.enrollment_date else None,
            'status': self.status,
            'final_score': self.final_score,
            'status_note': self.status_note
        }


class TeacherSubjectAssignment(db.Model):
    """Teacher assignment to SubjectGrade (asignacion de profesor a materia en grado)."""

    __tablename__ = 'teacher_subject_assignments'

    id = db.Column(db.Integer, primary_key=True)
    subject_grade_id = db.Column(db.Integer, db.ForeignKey('subject_grades.id'), nullable=False, unique=True, index=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    academic_year = db.Column(db.String(20), nullable=False, index=True)
    assignment_date = db.Column(db.Date, default=datetime.utcnow)
    status = db.Column(db.String(20), default='activo', index=True)  # activo, inactivo, temporal
    notes = db.Column(db.Text)

    # Relationships
    subject_grade = db.relationship('SubjectGrade', backref='teacher_assignment', lazy=True)
    teacher = db.relationship('User', backref='subject_assignments', lazy=True)

    def __repr__(self):
        return f'<TeacherSubjectAssignment {self.teacher.username} - {self.subject_grade.subject.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'subject_grade_id': self.subject_grade_id,
            'teacher_id': self.teacher_id,
            'academic_year': self.academic_year,
            'assignment_date': self.assignment_date.isoformat() if self.assignment_date else None,
            'status': self.status,
            'notes': self.notes
        }


class Schedule(db.Model):
    """Schedule entry for a SubjectGrade in a specific timeslot and classroom."""

    __tablename__ = 'schedules'

    id = db.Column(db.Integer, primary_key=True)
    subject_grade_id = db.Column(db.Integer, db.ForeignKey('subject_grades.id'), nullable=False, index=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), nullable=False, index=True)
    day_of_week = db.Column(db.Integer, nullable=False, index=True)  # 0=Lunes, 1=Martes, ..., 4=Viernes
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    academic_year = db.Column(db.String(20), nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, index=True)

    # Relationships
    subject_grade = db.relationship('SubjectGrade', backref='schedules', lazy=True)

    __table_args__ = (
        # Prevent classroom double-booking
        db.UniqueConstraint('classroom_id', 'day_of_week', 'start_time', 'academic_year', name='uq_schedule_classroom_time'),
    )

    def __repr__(self):
        days = ['Lun', 'Mar', 'Mie', 'Jue', 'Vie']
        day_name = days[self.day_of_week] if self.day_of_week < 5 else f'D{self.day_of_week}'
        return f'<Schedule {self.subject_grade.subject.name} - {day_name} {self.start_time}-{self.end_time}>'

    def get_day_name(self):
        """Get Spanish day name."""
        days = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']
        return days[self.day_of_week] if 0 <= self.day_of_week < 7 else f'Dia {self.day_of_week}'

    def to_dict(self):
        return {
            'id': self.id,
            'subject_grade_id': self.subject_grade_id,
            'classroom_id': self.classroom_id,
            'day_of_week': self.day_of_week,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'academic_year': self.academic_year,
            'is_active': self.is_active,
            'day_name': self.get_day_name()
        }


class ScheduleBlock(db.Model):
    """Time block definition for schedule generation (e.g., 7:00-8:00, 8:00-9:00)."""

    __tablename__ = 'schedule_blocks'

    id = db.Column(db.Integer, primary_key=True)
    campus_id = db.Column(db.Integer, db.ForeignKey('campuses.id'), nullable=False, index=True)
    name = db.Column(db.String(50), nullable=False)  # "Bloque 1", "Recreo"
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_break = db.Column(db.Boolean, default=False)  # Recreo/pause
    order_num = db.Column(db.Integer, default=0)  # Sort order
    academic_year = db.Column(db.String(20), nullable=False, index=True)

    # Relationships
    campus = db.relationship('Campus', backref='schedule_blocks', lazy=True)

    __table_args__ = (
        db.UniqueConstraint('campus_id', 'name', 'academic_year', name='uq_block_campus_name_year'),
    )

    def __repr__(self):
        return f'<ScheduleBlock {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'campus_id': self.campus_id,
            'name': self.name,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'is_break': self.is_break,
            'order_num': self.order_num,
            'academic_year': self.academic_year
        }
