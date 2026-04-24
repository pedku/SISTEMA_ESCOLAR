from datetime import datetime
from extensions import db

class QRToken(db.Model):
    """
    Model to store unique QR tokens for users.
    """
    __tablename__ = 'qr_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    token = db.Column(db.String(128), unique=True, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime)

    # Relationship
    user = db.relationship('User', backref=db.backref('qr_token_rel', uselist=False, lazy=True))

    def __repr__(self):
        return f'<QRToken user_id={self.user_id} active={self.is_active}>'

class QRAccessLog(db.Model):
    """
    Model to record every QR scan attempt.
    """
    __tablename__ = 'qr_access_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id', ondelete='SET NULL'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), nullable=False)  # 'authorized', 'denied', 'invalid_token', 'wrong_schedule'
    message = db.Column(db.String(255))
    ip_address = db.Column(db.String(45))  # Support IPv6

    # Relationships
    user = db.relationship('User', backref='qr_logs')
    classroom = db.relationship('Classroom', backref='access_logs')

    def __repr__(self):
        return f'<QRAccessLog user={self.user_id} status={self.status} time={self.timestamp}>'
