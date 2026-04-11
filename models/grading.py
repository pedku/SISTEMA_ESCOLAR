"""
Grading models: AcademicPeriod, GradeCriteria, GradeRecord, FinalGrade, AnnualGrade.
Handles the complete grading system.
"""

from datetime import datetime
from extensions import db


class AcademicPeriod(db.Model):
    """Academic period (e.g., Period 1, Period 2, etc.)."""
    
    __tablename__ = 'academic_periods'
    
    id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=False, index=True)
    name = db.Column(db.String(50), nullable=False)
    short_name = db.Column(db.String(10), nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=False)
    academic_year = db.Column(db.String(20), nullable=False, index=True)
    order = db.Column(db.Integer, nullable=False)
    
    # Relationships
    grade_records = db.relationship('GradeRecord', backref='period', lazy='dynamic', cascade='all, delete-orphan')
    final_grades = db.relationship('FinalGrade', backref='period', lazy='dynamic', cascade='all, delete-orphan')
    report_cards = db.relationship('ReportCard', backref='period', lazy='dynamic', cascade='all, delete-orphan')
    student_achievements = db.relationship('StudentAchievement', backref='period', lazy='dynamic', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.UniqueConstraint('institution_id', 'short_name', 'academic_year', name='uq_period_inst_year'),
    )
    
    def __repr__(self):
        return f'<AcademicPeriod {self.name} - {self.academic_year}>'
    
    def to_dict(self):
        """Convert academic period to dictionary."""
        return {
            'id': self.id,
            'institution_id': self.institution_id,
            'name': self.name,
            'short_name': self.short_name,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_active': self.is_active,
            'academic_year': self.academic_year,
            'order': self.order
        }


class GradeCriteria(db.Model):
    """Evaluation criteria with weight percentages."""
    
    __tablename__ = 'grade_criteria'
    
    id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    weight = db.Column(db.Float, nullable=False)  # Percentage weight (e.g., 20.0, 30.0)
    description = db.Column(db.String(300))
    order = db.Column(db.Integer, nullable=False)
    
    # Relationships
    grade_records = db.relationship('GradeRecord', backref='criterion', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<GradeCriteria {self.name} ({self.weight}%)>'
    
    def to_dict(self):
        """Convert grade criteria to dictionary."""
        return {
            'id': self.id,
            'institution_id': self.institution_id,
            'name': self.name,
            'weight': self.weight,
            'description': self.description,
            'order': self.order
        }


class GradeRecord(db.Model):
    """Individual grade record for a student, subject-grade, period, and criterion."""
    
    __tablename__ = 'grade_records'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('academic_students.id'), nullable=False, index=True)
    subject_grade_id = db.Column(db.Integer, db.ForeignKey('subject_grades.id'), nullable=False, index=True)
    period_id = db.Column(db.Integer, db.ForeignKey('academic_periods.id'), nullable=False, index=True)
    criterion_id = db.Column(db.Integer, db.ForeignKey('grade_criteria.id'), nullable=False, index=True)
    score = db.Column(db.Float(5, 2), nullable=False)  # 1.0 - 5.0
    observation = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    locked = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<GradeRecord Student:{self.student_id} SG:{self.subject_grade_id} P:{self.period_id} = {self.score}>'
    
    def to_dict(self):
        """Convert grade record to dictionary."""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'subject_grade_id': self.subject_grade_id,
            'period_id': self.period_id,
            'criterion_id': self.criterion_id,
            'score': self.score,
            'observation': self.observation,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'locked': self.locked
        }


class FinalGrade(db.Model):
    """Final calculated grade for a student, subject-grade, and period."""
    
    __tablename__ = 'final_grades'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('academic_students.id'), nullable=False, index=True)
    subject_grade_id = db.Column(db.Integer, db.ForeignKey('subject_grades.id'), nullable=False, index=True)
    period_id = db.Column(db.Integer, db.ForeignKey('academic_periods.id'), nullable=False, index=True)
    final_score = db.Column(db.Float(5, 2), nullable=False)
    status = db.Column(db.String(20), default='no evaluado')  # ganada, perdida, no evaluado
    observation = db.Column(db.String(500))
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<FinalGrade Student:{self.student_id} SG:{self.subject_grade_id} P:{self.period_id} = {self.final_score}>'
    
    def to_dict(self):
        """Convert final grade to dictionary."""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'subject_grade_id': self.subject_grade_id,
            'period_id': self.period_id,
            'final_score': self.final_score,
            'status': self.status,
            'observation': self.observation,
            'calculated_at': self.calculated_at.isoformat() if self.calculated_at else None
        }


class AnnualGrade(db.Model):
    """Annual definitive grade for a student and subject-grade."""
    
    __tablename__ = 'annual_grades'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('academic_students.id'), nullable=False, index=True)
    subject_grade_id = db.Column(db.Integer, db.ForeignKey('subject_grades.id'), nullable=False, index=True)
    annual_score = db.Column(db.Float(5, 2), nullable=False)
    status = db.Column(db.String(20), default='no evaluado')  # aprobado, reprobado
    academic_year = db.Column(db.String(20), nullable=False, index=True)
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'subject_grade_id', 'academic_year', name='uq_annual_student_subject_year'),
    )
    
    def __repr__(self):
        return f'<AnnualGrade Student:{self.student_id} SG:{self.subject_grade_id} Y:{self.academic_year} = {self.annual_score}>'
    
    def to_dict(self):
        """Convert annual grade to dictionary."""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'subject_grade_id': self.subject_grade_id,
            'annual_score': self.annual_score,
            'status': self.status,
            'academic_year': self.academic_year
        }
