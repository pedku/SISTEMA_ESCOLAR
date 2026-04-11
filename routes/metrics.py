"""
Metrics and analytics routes.
"""

from flask import Blueprint, render_template

metrics_bp = Blueprint('metrics', __name__, url_prefix='/')


@metrics_bp.route('/metrics/teacher')
def teacher_metrics():
    """View teacher-specific metrics."""
    return render_template('metrics/teacher.html')


@metrics_bp.route('/metrics/institution')
def institution_metrics():
    """View institution-wide metrics."""
    return render_template('metrics/institution.html')


@metrics_bp.route('/metrics/heatmap')
def metrics_heatmap():
    """View performance heatmap."""
    return render_template('metrics/heatmap.html')


@metrics_bp.route('/metrics/risk-students')
def risk_students():
    """View students at risk."""
    return render_template('metrics/risk_students.html')
