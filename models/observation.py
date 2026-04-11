"""
Observation model for behavior and academic observations.
"""

from datetime import datetime
from extensions import db


class Observation(db.Model):
    """Student observation (behavior, academic, etc.)."""
    
    __tablename__ = 'observations'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('academic_students.id'), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    type = db.Column(db.String(20), nullable=False)
    # 'positiva', 'negativa', 'seguimiento', 'convivencia'
    category = db.Column(db.String(50))
    # "Disciplina", "Rendimiento", "Valores", etc.
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    commitments = db.Column(db.Text)
    notified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Observation Student:{self.student_id} Type:{self.type} Date:{self.date}>'
    
    def is_positive(self):
        """Check if observation is positive."""
        return self.type == 'positiva'
    
    def is_negative(self):
        """Check if observation is negative."""
        return self.type == 'negativa'
    
    def requires_notification(self):
        """Check if this observation requires parent notification."""
        return self.type in ['negativa', 'convivencia']
    
    def to_dict(self):
        """Convert observation to dictionary."""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'author_id': self.author_id,
            'type': self.type,
            'category': self.category,
            'description': self.description,
            'date': self.date.isoformat() if self.date else None,
            'commitments': self.commitments,
            'notified': self.notified,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
