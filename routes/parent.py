"""
Parent portal routes.
"""

from flask import Blueprint, render_template

parent_bp = Blueprint('parent', __name__)


@parent_bp.route('/dashboard')
def parent_dashboard():
    """Parent portal dashboard."""
    return render_template('parent/dashboard.html')


@parent_bp.route('/grades/<int:student_id>')
def parent_view_grades(student_id):
    """View grades for parent's student."""
    return render_template('parent/grades.html', student_id=student_id)


@parent_bp.route('/attendance/<int:student_id>')
def parent_view_attendance(student_id):
    """View attendance for parent's student."""
    return render_template('parent/attendance.html', student_id=student_id)


@parent_bp.route('/report-cards/<int:student_id>')
def parent_view_report_cards(student_id):
    """View report cards for parent's student."""
    return render_template('parent/report_cards.html', student_id=student_id)
