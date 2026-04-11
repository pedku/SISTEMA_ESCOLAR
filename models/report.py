"""
Report card models for generating and storing student report cards.
"""

from datetime import datetime
from extensions import db


class ReportCard(db.Model):
    """Student report card for a specific period."""
    
    __tablename__ = 'report_cards'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('academic_students.id'), nullable=False, index=True)
    period_id = db.Column(db.Integer, db.ForeignKey('academic_periods.id'), nullable=False, index=True)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    pdf_path = db.Column(db.String(300))
    general_observation = db.Column(db.Text)
    generated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    delivery_status = db.Column(db.String(20), default='pendiente')
    # 'pendiente', 'entregado'
    delivery_date = db.Column(db.Date)
    
    # Relationships
    subject_observations = db.relationship('ReportCardObservation', backref='report_card', lazy='dynamic', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'period_id', name='uq_report_card_student_period'),
    )
    
    def __repr__(self):
        return f'<ReportCard Student:{self.student_id} Period:{self.period_id}>'
    
    def is_delivered(self):
        """Check if report card has been delivered."""
        return self.delivery_status == 'entregado'
    
    def to_dict(self):
        """Convert report card to dictionary."""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'period_id': self.period_id,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'pdf_path': self.pdf_path,
            'general_observation': self.general_observation,
            'generated_by': self.generated_by,
            'delivery_status': self.delivery_status,
            'delivery_date': self.delivery_date.isoformat() if self.delivery_date else None
        }


class ReportCardObservation(db.Model):
    """Subject-specific observation for a report card."""
    
    __tablename__ = 'report_card_observations'
    
    id = db.Column(db.Integer, primary_key=True)
    report_card_id = db.Column(db.Integer, db.ForeignKey('report_cards.id'), nullable=False, index=True)
    subject_grade_id = db.Column(db.Integer, db.ForeignKey('subject_grades.id'), nullable=False, index=True)
    observation = db.Column(db.String(500), nullable=False)
    
    def __repr__(self):
        return f'<ReportCardObservation RC:{self.report_card_id} SG:{self.subject_grade_id}>'
    
    def to_dict(self):
        """Convert report card observation to dictionary."""
        return {
            'id': self.id,
            'report_card_id': self.report_card_id,
            'subject_grade_id': self.subject_grade_id,
            'observation': self.observation
        }
