"""
Academic models: GradeLevel, Grade, Subject, SubjectGrade, AcademicStudent.
Handles the academic structure of the institution.
"""

from datetime import datetime
from extensions import db


class GradeLevel(db.Model):
    """Academic level (e.g., 'Primero', 'Sexto', 'Once').
    Groups courses/grades within a campus.
    Hierarchy: Institution → Campus → GradeLevel → Grade (course).
    """

    __tablename__ = 'grade_levels'

    id = db.Column(db.Integer, primary_key=True)
    campus_id = db.Column(db.Integer, db.ForeignKey('campuses.id'), nullable=False, index=True)
    name = db.Column(db.String(50), nullable=False)  # "Primero", "Sexto", "Once"
    order_num = db.Column(db.Integer, default=0)  # For sorting levels in order

    # Relationships
    grades = db.relationship('Grade', backref='level', lazy='dynamic', cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('campus_id', 'name', name='uq_gradelevel_campus_name'),
    )

    def __repr__(self):
        return f'<GradeLevel {self.name}>'

    def to_dict(self):
        """Convert grade level to dictionary."""
        return {
            'id': self.id,
            'campus_id': self.campus_id,
            'name': self.name,
            'order_num': self.order_num,
            'course_count': self.grades.count()
        }


class Grade(db.Model):
    """Course/Group model (e.g., "6-01", "11°B").
    Represents a specific group within a GradeLevel.
    """
    
    __tablename__ = 'grades'
    
    id = db.Column(db.Integer, primary_key=True)
    campus_id = db.Column(db.Integer, db.ForeignKey('campuses.id'), nullable=False, index=True)
    level_id = db.Column(db.Integer, db.ForeignKey('grade_levels.id', ondelete='SET NULL'), nullable=True, index=True)
    director_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    name = db.Column(db.String(50), nullable=False)
    academic_year = db.Column(db.String(20), nullable=False, index=True)
    shift = db.Column(db.String(20), default='Mañana', index=True)  # Mañana, Tarde, Nocturna, Única, Sabatina
    max_students = db.Column(db.Integer, default=40)
    
    # Relationships
    subject_grades = db.relationship('SubjectGrade', backref='grade', lazy='dynamic', cascade='all, delete-orphan')
    academic_students = db.relationship('AcademicStudent', backref='grade', lazy='dynamic', cascade='save-update, merge')
    
    __table_args__ = (
        db.UniqueConstraint('campus_id', 'name', 'academic_year', 'shift', name='uq_grade_campus_year_shift'),
    )
    
    def __repr__(self):
        return f'<Grade {self.name} - {self.academic_year}>'
    
    def get_student_count(self):
        """Get number of students in this grade."""
        return self.academic_students.filter_by(status='activo').count()
    
    def to_dict(self):
        """Convert grade to dictionary."""
        return {
            'id': self.id,
            'campus_id': self.campus_id,
            'director_id': self.director_id,
            'name': self.name,
            'academic_year': self.academic_year,
            'max_students': self.max_students,
            'student_count': self.get_student_count()
        }


class Subject(db.Model):
    """Subject model (e.g., "Matemáticas", "Ciencias Naturales")."""

    __tablename__ = 'subjects'

    id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), index=True)

    # Relationships
    institution = db.relationship('Institution', backref=db.backref('subjects', lazy='dynamic', cascade='all, delete-orphan'), foreign_keys=[institution_id])
    subject_grades = db.relationship('SubjectGrade', backref='subject', lazy='dynamic', cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('institution_id', 'code', name='uq_subject_institution_code'),
    )
    
    def __repr__(self):
        return f'<Subject {self.name}>'
    
    def to_dict(self):
        """Convert subject to dictionary."""
        return {
            'id': self.id,
            'institution_id': self.institution_id,
            'name': self.name,
            'code': self.code
        }


class SubjectGrade(db.Model):
    """Association between Subject, Grade, and Teacher."""
    
    __tablename__ = 'subject_grades'
    
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False, index=True)
    grade_id = db.Column(db.Integer, db.ForeignKey('grades.id'), nullable=False, index=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    hours_per_week = db.Column(db.Integer, default=4)
    
    # Relationships
    grade_records = db.relationship('GradeRecord', backref='subject_grade', lazy='dynamic', cascade='all, delete-orphan')
    final_grades = db.relationship('FinalGrade', backref='subject_grade', lazy='dynamic', cascade='all, delete-orphan')
    annual_grades = db.relationship('AnnualGrade', backref='subject_grade', lazy='dynamic', cascade='all, delete-orphan')
    attendance_records = db.relationship('Attendance', lazy='dynamic', cascade='all, delete-orphan')
    report_card_observations = db.relationship('ReportCardObservation', backref='subject_grade', lazy='dynamic', cascade='all, delete-orphan')
    # Note: enrollments, teacher_assignment, and schedules relationships are defined in models/scheduling.py
    
    __table_args__ = (
        db.UniqueConstraint('subject_id', 'grade_id', 'teacher_id', name='uq_subject_grade_teacher'),
    )
    
    def __repr__(self):
        return f'<SubjectGrade {self.subject.name} - {self.grade.name}>'
    
    def to_dict(self):
        """Convert subject-grade to dictionary."""
        return {
            'id': self.id,
            'subject_id': self.subject_id,
            'grade_id': self.grade_id,
            'teacher_id': self.teacher_id,
            'subject_name': self.subject.name,
            'grade_name': self.grade.name,
            'teacher_name': self.teacher_user.get_full_name() if self.teacher_user else None
        }


class AcademicStudent(db.Model):
    """Academic student profile linking to User."""
    
    __tablename__ = 'academic_students'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, index=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=False, index=True)
    campus_id = db.Column(db.Integer, db.ForeignKey('campuses.id'), nullable=False, index=True)
    grade_id = db.Column(db.Integer, db.ForeignKey('grades.id', ondelete='SET NULL'), nullable=True, index=True)
    neighborhood = db.Column(db.String(100))
    stratum = db.Column(db.Integer)
    blood_type = db.Column(db.String(5))
    eps = db.Column(db.String(100))
    guardian_name = db.Column(db.String(150))
    guardian_phone = db.Column(db.String(20))
    guardian_email = db.Column(db.String(100))
    enrolled_year = db.Column(db.String(20))
    status = db.Column(db.String(20), default='activo', index=True)  # activo, retirado, graduado
    
    # Relationships
    # grade relationship is provided via backref from Grade.academic_students
    grade_records = db.relationship('GradeRecord', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    final_grades = db.relationship('FinalGrade', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    annual_grades = db.relationship('AnnualGrade', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    attendance_records = db.relationship('Attendance', lazy='dynamic', cascade='all, delete-orphan', foreign_keys='Attendance.student_id')
    observations = db.relationship('Observation', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    report_cards = db.relationship('ReportCard', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    achievements = db.relationship('StudentAchievement', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    parent_students = db.relationship('ParentStudent', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    alerts = db.relationship('Alert', lazy='dynamic', cascade='all, delete-orphan')
    enrollments = db.relationship('StudentEnrollment', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<AcademicStudent {self.user.username if self.user else self.id}>'
    
    def get_current_average(self):
        """Get current average grade across all subjects."""
        # This would need to be calculated via FinalGrade or GradeRecord
        # Implementation would go in a service
        pass
    
    def to_dict(self):
        """Convert academic student to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'institution_id': self.institution_id,
            'campus_id': self.campus_id,
            'grade_id': self.grade_id,
            'neighborhood': self.neighborhood,
            'stratum': self.stratum,
            'blood_type': self.blood_type,
            'eps': self.eps,
            'guardian_name': self.guardian_name,
            'guardian_phone': self.guardian_phone,
            'guardian_email': self.guardian_email,
            'enrolled_year': self.enrolled_year,
            'status': self.status
        }


class ParentStudent(db.Model):
    """Association between parents and students."""
    
    __tablename__ = 'parent_students'
    
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('academic_students.id'), nullable=False, index=True)
    relationship = db.Column(db.String(50))  # Padre, Madre, Acudiente, etc.
    
    __table_args__ = (
        db.UniqueConstraint('parent_id', 'student_id', name='uq_parent_student'),
    )
    
    def __repr__(self):
        return f'<ParentStudent {self.parent_id} -> {self.student_id}>'
