"""
Institution and Campus models.
Handles multi-institution and multi-campus support.
"""

from datetime import datetime
from extensions import db


class Institution(db.Model):
    """Educational institution model."""
    
    __tablename__ = 'institutions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    nit = db.Column(db.String(20), unique=True, index=True)
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    logo = db.Column(db.String(200))
    municipality = db.Column(db.String(100))
    department = db.Column(db.String(100))
    resolution = db.Column(db.String(100))
    academic_year = db.Column(db.String(20), default='2026')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    campuses = db.relationship('Campus', backref='institution', lazy='dynamic', cascade='all, delete-orphan')
    academic_periods = db.relationship('AcademicPeriod', backref='institution', lazy='dynamic', cascade='all, delete-orphan')
    grade_criteria = db.relationship('GradeCriteria', backref='institution', lazy='dynamic', cascade='all, delete-orphan')
    academic_students = db.relationship('AcademicStudent', backref='institution', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Institution {self.name}>'
    
    def to_dict(self):
        """Convert institution to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'nit': self.nit,
            'address': self.address,
            'phone': self.phone,
            'email': self.email,
            'logo': self.logo,
            'municipality': self.municipality,
            'department': self.department,
            'resolution': self.resolution,
            'academic_year': self.academic_year,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Campus(db.Model):
    """Campus/Sede of an institution."""

    __tablename__ = 'campuses'

    id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    code = db.Column(db.String(20), index=True)
    address = db.Column(db.String(200))
    jornada = db.Column(db.String(50), default='completa')  # mañana, tarde, completa
    is_main_campus = db.Column(db.Boolean, default=False)  # Solo una sede principal por institución
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    grades = db.relationship('Grade', backref='campus', lazy='dynamic', cascade='all, delete-orphan')
    grade_levels = db.relationship('GradeLevel', backref='campus', lazy='dynamic', cascade='all, delete-orphan')
    classrooms = db.relationship('Classroom', backref='campus', lazy='dynamic', cascade='all, delete-orphan')
    schedule_blocks = db.relationship('ScheduleBlock', backref='campus', lazy='dynamic', cascade='all, delete-orphan')
    academic_students = db.relationship('AcademicStudent', backref='campus', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Campus {self.name}>'

    def to_dict(self):
        """Convert campus to dictionary."""
        return {
            'id': self.id,
            'institution_id': self.institution_id,
            'name': self.name,
            'code': self.code,
            'address': self.address,
            'jornada': self.jornada,
            'is_main_campus': self.is_main_campus,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
