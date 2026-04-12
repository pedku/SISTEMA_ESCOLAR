"""
Metrics and analytics routes.
"""

from flask import Blueprint, render_template

metrics_bp = Blueprint('metrics', __name__)


@metrics_bp.route('/teacher')
def teacher_metrics():
    """View teacher-specific metrics."""
    return render_template('metrics/teacher.html')


@metrics_bp.route('/institution')
def institution_metrics():
    """View institution-wide metrics."""
    return render_template('metrics/institution.html')


@metrics_bp.route('/heatmap')
def metrics_heatmap():
    """View performance heatmap."""
    return render_template('metrics/heatmap.html')


@metrics_bp.route('/risk-students')
def risk_students():
    """View students at risk."""
    return render_template('metrics/risk_students.html')
