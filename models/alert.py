"""
Alert model for early warning system (Alertas Tempranas).
Tracks academic risk, attendance issues, and positive improvements.
"""

from datetime import datetime
from extensions import db


class Alert(db.Model):
    """Early warning alert for students or groups."""

    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('academic_students.id'), nullable=False, index=True)
    alert_type = db.Column(db.String(50), nullable=False, index=True)
    # 'riesgo_academico', 'tendencia_negativa', 'inasistencia_critica',
    # 'grupo_riesgo', 'riesgo_desercion', 'mejora_destacable'
    severity = db.Column(db.String(20), nullable=False)
    # 'alta', 'media', 'baja'
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    triggered_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    resolved = db.Column(db.Boolean, default=False, index=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    notes = db.Column(db.Text, nullable=True)

    # Relationships
    student = db.relationship('AcademicStudent', backref='alerts', lazy='joined')
    resolver = db.relationship('User', foreign_keys=[resolved_by], lazy='joined')

    def __repr__(self):
        return f'<Alert {self.alert_type} [{self.severity}] Student:{self.student_id}>'

    @property
    def is_resolved(self):
        """Check if alert is resolved."""
        return self.resolved

    @property
    def severity_color(self):
        """Get Bootstrap color class for severity."""
        colors = {
            'alta': 'danger',
            'media': 'warning',
            'baja': 'success'
        }
        return colors.get(self.severity, 'secondary')

    @property
    def severity_icon(self):
        """Get Bootstrap icon for severity."""
        icons = {
            'alta': 'exclamation-triangle-fill',
            'media': 'exclamation-circle',
            'baja': 'check-circle'
        }
        return icons.get(self.severity, 'info-circle')

    @property
    def alert_type_label(self):
        """Get display label for alert type."""
        labels = {
            'riesgo_academico': 'Riesgo Academico',
            'tendencia_negativa': 'Tendencia Negativa',
            'inasistencia_critica': 'Inasistencia Critica',
            'grupo_riesgo': 'Grupo en Riesgo',
            'riesgo_desercion': 'Riesgo de Desercion',
            'mejora_destacable': 'Mejora Destacable'
        }
        return labels.get(self.alert_type, self.alert_type)

    @property
    def alert_type_icon(self):
        """Get Bootstrap icon for alert type."""
        icons = {
            'riesgo_academico': 'book',
            'tendencia_negativa': 'graph-down-arrow',
            'inasistencia_critica': 'calendar-x',
            'grupo_riesgo': 'people',
            'riesgo_desercion': 'person-x',
            'mejora_destacable': 'graph-up-arrow'
        }
        return icons.get(self.alert_type, 'exclamation-triangle')

    def to_dict(self):
        """Convert alert to dictionary."""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.user.get_full_name() if self.student and self.student.user else 'Desconocido',
            'alert_type': self.alert_type,
            'alert_type_label': self.alert_type_label,
            'severity': self.severity,
            'title': self.title,
            'description': self.description,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'resolved': self.resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by,
            'notes': self.notes
        }
