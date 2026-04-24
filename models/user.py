"""
User model for authentication and authorization.
Supports multiple roles: root, admin, coordinator, teacher, student, parent, viewer
"""

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, login_manager


class User(UserMixin, db.Model):
    """User model for system authentication and management."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    document_type = db.Column(db.String(20), default='CC')  # CC, TI, RC, Pasaporte
    document_number = db.Column(db.String(30), unique=True, index=True)
    birth_date = db.Column(db.Date)
    gender = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    country = db.Column(db.String(50))
    department = db.Column(db.String(100))
    municipality = db.Column(db.String(100))
    role = db.Column(db.String(20), nullable=False, index=True)  # root, admin, coordinator, teacher, student, parent, viewer
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=True, index=True)
    photo = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    must_change_password = db.Column(db.Boolean)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # Institution relationship
    institution = db.relationship('Institution', backref='users', foreign_keys=[institution_id])

    # As director de grupo
    directed_grades = db.relationship('Grade', backref='director_user', lazy='dynamic', foreign_keys='Grade.director_id')
    
    # As teacher
    subject_grades = db.relationship('SubjectGrade', backref='teacher_user', lazy='dynamic', foreign_keys='SubjectGrade.teacher_id')
    
    # As student
    academic_student = db.relationship('AcademicStudent', backref='user', uselist=False, foreign_keys='AcademicStudent.user_id')
    
    # As parent
    parent_students = db.relationship('ParentStudent', backref='parent_user', lazy='dynamic', foreign_keys='ParentStudent.parent_id')
    
    # Observations authored
    authored_observations = db.relationship('Observation', backref='author', lazy='dynamic', foreign_keys='Observation.author_id')
    
    # Grades created
    created_grades = db.relationship('GradeRecord', backref='creator', lazy='dynamic', foreign_keys='GradeRecord.created_by')
    
    # Attendance recorded
    recorded_attendance = db.relationship('Attendance', backref='recorder', lazy='dynamic', foreign_keys='Attendance.recorded_by')
    
    def set_password(self, password):
        """Hash and store password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password against stored hash."""
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def name(self):
        """Get user's full name (alias for get_full_name)."""
        return self.get_full_name()

    def has_role(self, role):
        """Check if user has specific role."""
        return self.role == role
    
    def has_any_role(self, *roles):
        """Check if user has any of the specified roles."""
        return self.role in roles
    
    def is_root(self):
        return self.role == 'root'
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_coordinator(self):
        return self.role == 'coordinator'
    
    def is_teacher(self):
        return self.role == 'teacher'
    
    def is_student(self):
        return self.role == 'student'
    
    def is_parent(self):
        return self.role == 'parent'
    
    def is_viewer(self):
        return self.role == 'viewer'
    
    def can_edit_grades(self):
        """Check if user can edit grades."""
        return self.role in ['root', 'admin', 'teacher']
    
    def can_view_all_grades(self):
        """Check if user can view all grades."""
        return self.role in ['root', 'admin', 'coordinator']

    def get_institution(self):
        """Get the institution this user belongs to.
        For root users, returns None (they can access all institutions).
        """
        return self.institution

    def can_access_institution(self, institution_id):
        """Check if user can access a specific institution.
        Root users can access all, others only their assigned institution.
        """
        if self.is_root():
            return True
        return self.institution_id == institution_id
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'role': self.role,
            'institution_id': self.institution_id,
            'institution_name': self.institution.name if self.institution else None,
            'document_type': self.document_type,
            'document_number': self.document_number,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'gender': self.gender,
            'phone': self.phone,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
