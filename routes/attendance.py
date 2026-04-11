"""
Attendance management routes.
"""

from flask import Blueprint, render_template

attendance_bp = Blueprint('attendance', __name__, url_prefix='/')


@attendance_bp.route('/attendance')
def attendance():
    """Take attendance."""
    return render_template('attendance/take.html')


@attendance_bp.route('/attendance/student/<int:id>')
def student_attendance_history(id):
    """View attendance history for a student."""
    return render_template('attendance/summary.html', student_id=id)
