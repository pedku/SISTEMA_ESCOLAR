"""
Attendance model for academic attendance tracking.
"""

from datetime import datetime
from extensions import db


class Attendance(db.Model):
    """Student attendance record."""
    
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('academic_students.id'), nullable=False, index=True)
    subject_grade_id = db.Column(db.Integer, db.ForeignKey('subject_grades.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='presente')
    # 'presente', 'ausente', 'justificado', 'excusado'
    observation = db.Column(db.String(300))
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Attendance Student:{self.student_id} Date:{self.date} Status:{self.status}>'
    
    def is_absent(self):
        """Check if attendance is absent."""
        return self.status == 'ausente'
    
    def is_justified(self):
        """Check if absence is justified."""
        return self.status in ['justificado', 'excusado']
    
    def to_dict(self):
        """Convert attendance to dictionary."""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'subject_grade_id': self.subject_grade_id,
            'date': self.date.isoformat() if self.date else None,
            'status': self.status,
            'observation': self.observation,
            'recorded_by': self.recorded_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
