"""
Achievement models for gamification system.
"""

from datetime import datetime
from extensions import db


class Achievement(db.Model):
    """Achievement/Badge that students can earn."""

    __tablename__ = 'achievements'

    id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=True, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=False)
    icon = db.Column(db.String(100))  # Icon/emoji or path to icon
    criteria = db.Column(db.String(200))  # Description of criteria to earn
    category = db.Column(db.String(50))
    # 'académico', 'asistencia', 'comportamiento', 'mejora'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    institution = db.relationship('Institution', backref='achievements', foreign_keys=[institution_id])
    student_achievements = db.relationship('StudentAchievement', backref='achievement', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Achievement {self.name}>'
    
    def to_dict(self):
        """Convert achievement to dictionary."""
        return {
            'id': self.id,
            'institution_id': self.institution_id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'criteria': self.criteria,
            'category': self.category,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class StudentAchievement(db.Model):
    """Achievement earned by a student."""
    
    __tablename__ = 'student_achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('academic_students.id'), nullable=False, index=True)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id'), nullable=False, index=True)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    period_id = db.Column(db.Integer, db.ForeignKey('academic_periods.id'), index=True)
    awarded_by = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    
    def __repr__(self):
        return f'<StudentAchievement Student:{self.student_id} Achievement:{self.achievement_id}>'
    
    def to_dict(self):
        """Convert student achievement to dictionary."""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'achievement_id': self.achievement_id,
            'achievement_name': self.achievement.name if self.achievement else None,
            'earned_at': self.earned_at.isoformat() if self.earned_at else None,
            'period_id': self.period_id
        }
