"""
Observation management routes.
"""

from flask import Blueprint, render_template

observations_bp = Blueprint('observations', __name__, url_prefix='/')


@observations_bp.route('/observations')
def observations():
    """Create and view observations."""
    return render_template('observations/create.html')


@observations_bp.route('/observations/student/<int:id>')
def student_observations(id):
    """View observation history for a student."""
    return render_template('observations/student_history.html', student_id=id)
